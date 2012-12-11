#include <Arduino.h>
#include <LiquidCrystal.h>

// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(2, 3, 10, 11, 12, 13);

// initialize some settings
int pins[]={A4,A2,A1,A0};	// pins used for buttons
int numPins=4;				// number of buttons
int writeDelay=250;			// used after each serial write
int pressDelay=50;			// used to space out multi-button presses
int baud=9600;				// baud rate for serial communication
int requestRate=3000;		// how frequently we should poll the computer for data

// initialize some timers
unsigned long lastUpdate=0;
unsigned long lastReceived=0;

// send a value and delay slightly
void writeVal(int val) {
	Serial.println(val);
	delay(writeDelay);
}

// check the button pins and return
// their binary combination
int checkPins() {
	int pressed=0;
	for(int i=0;i<numPins;i++) pressed |= digitalRead(pins[i])<<i;
	return pressed;
}

void setup() {
	// set up the LCD's number of columns and rows
	lcd.begin(16,2);

	// set up button pins
	for(int i=0;i<numPins;i++) pinMode(pins[i],INPUT);

	// set up serial
	Serial.begin(baud);

	// tell the user we're okay!
	lcd.clear();
	lcd.print("Okay!");
	delay(1000);
	lcd.clear();

	// set the timers
	lastUpdate=millis();
	lastReceived=millis();
}

void loop() {
	// if we've got datas available...
	if(Serial.available()) {
		// wait for the full message
		delay(100);

		// reset LCD
		lcd.clear();

		// read bytes!
		while(Serial.available()>0) {
			int y=Serial.read();

			if((char)y=='\n') lcd.setCursor(0,1); // newline
			else if((char)y=='\t') break; // end of signal
			else lcd.print((char)y); // print it
		}
		
		// update timers
		lastUpdate=millis();
		lastReceived=millis();

	} else { // otherwise...
		// if we haven't had a new display in a while,
		// request the default display
		if((millis()-requestRate) >= lastUpdate) {
			writeVal(-1);
			lastUpdate=millis();
		}
		// if we haven't had a new response in a while,
		// we're probably disconnected
		if((millis()-requestRate*2) >= lastReceived) {
			lcd.clear();
			lcd.print("(disconnected)");
			lcd.setCursor(0,1);
			lcd.print("0"); // error code
			delay(1000);
		}
	}

	// checks buttons and writes their states if any are down
	int x=0;
	checkPins() && (delay(pressDelay),true) && (x=checkPins()) && (writeVal(x),true);
}

int main() {
	init();
	setup();
	while(true) loop();
	return 1;
}