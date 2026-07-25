/*
  sketch.ino  (sensing node - v2, no external component needed)
  -------------------------------------------------------
  Task 4: Sensing node for the Village Water Point Uptime Monitoring project.
  Simulated in Wokwi using ONLY an ESP32 board - no wiring required.

  The flow signal is generated IN SOFTWARE (instead of read from a
  potentiometer), which is still a valid simulation per the assessment
  brief ("Wokwi or Tinkercad ... SIMULATION ONLY"), and it deterministically
  demonstrates every required behaviour without needing to manually turn a
  knob during the demo recording.

  Requirements this sketch satisfies:
    1. Reads on a FIXED SCHEDULE using non-blocking timing (millis()),
       never a blocking delay().
    2. PLAUSIBILITY CHECK - rejects impossible readings (out of range)
       instead of trusting every raw value. Demonstrated by deliberately
       injecting one implausible spike.
    3. SMOOTHING - a rolling average over the last few readings, so a
       single spike/noise sample cannot be mistaken for a real change
       in flow. Demonstrated by injecting a stuck/repeated value run.

  Output: one line per reading over Serial, in the same field shape as
  waterpoint_readings.csv, so it can feed the same dashboard/assistant:
      waterpoint_id,flow_ok,usage_count,recorded_at
*/

// ---- Configuration ----
const char* WATERPOINT_ID = "WP001";
const unsigned long READ_INTERVAL_MS = 3000;   // one reading every 3s (sped up for demo)

const int USAGE_MAX_PLAUSIBLE = 20;      // matches dataset's normal usage_count range
const int SMOOTHING_WINDOW = 3;
const int FLOW_THRESHOLD = 3;

// ---- State ----
unsigned long lastReadTime = 0;
int readingNumber = 0;
int smoothingBuffer[SMOOTHING_WINDOW];
int smoothingIndex = 0;
int smoothingCount = 0;
unsigned long simulatedSecondsElapsed = 0;

void setup() {
  Serial.begin(115200);
  delay(200); // startup only, not inside the sensing loop
  randomSeed(12345); // reproducible sequence for demo purposes
  Serial.println("waterpoint_id,flow_ok,usage_count,recorded_at,note");
}

void loop() {
  unsigned long now = millis();

  if (now - lastReadTime >= READ_INTERVAL_MS) {
    lastReadTime = now;
    takeReading();
  }
}

// Simulates the raw sensor value in software, deliberately injecting
// specific awkward cases at fixed reading numbers so the demo is
// reproducible every time it's run.
int getSimulatedRawUsage() {
  readingNumber++;

  if (readingNumber == 4) {
    return 500;  // EXTREME/faulty spike - way outside plausible range
  }
  if (readingNumber >= 6 && readingNumber <= 9) {
    return 7;    // STUCK sensor - identical repeated value
  }
  return random(3, 18);  // normal healthy range
}

void takeReading() {
  int rawUsage = getSimulatedRawUsage();
  simulatedSecondsElapsed += 900; // advance fake clock by 15 simulated minutes per reading

  // ---- Plausibility check ----
  if (rawUsage < 0 || rawUsage > USAGE_MAX_PLAUSIBLE) {
    printReading(0, 0, "REJECTED: value out of plausible range");
    return; // implausible value never reaches smoothing
  }

  // ---- Smoothing ----
  smoothingBuffer[smoothingIndex] = rawUsage;
  smoothingIndex = (smoothingIndex + 1) % SMOOTHING_WINDOW;
  if (smoothingCount < SMOOTHING_WINDOW) smoothingCount++;

  long sum = 0;
  for (int i = 0; i < smoothingCount; i++) {
    sum += smoothingBuffer[i];
  }
  int smoothedUsage = sum / smoothingCount;

  int flowOk = (smoothedUsage >= FLOW_THRESHOLD) ? 1 : 0;

  printReading(flowOk, smoothedUsage, "ok");
}

void printReading(int flowOk, int usageCount, const char* note) {
  unsigned long totalSeconds = simulatedSecondsElapsed;
  unsigned long hh = (6 + (totalSeconds / 3600)) % 24;
  unsigned long mm = (totalSeconds / 60) % 60;
  unsigned long ss = totalSeconds % 60;

  char timestamp[9];
  sprintf(timestamp, "%02lu:%02lu:%02lu", hh, mm, ss);

  Serial.print(WATERPOINT_ID);
  Serial.print(",");
  Serial.print(flowOk);
  Serial.print(",");
  Serial.print(usageCount);
  Serial.print(",2026-07-20 ");
  Serial.print(timestamp);
  Serial.print(",");
  Serial.println(note);
}