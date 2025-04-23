// Global variables
let model, maxPredictions;
let isListening = false;
let attendanceRecords = {};

// DOM elements
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const statusDisplay = document.getElementById('status');
const attendanceList = document.getElementById('attendanceList');

// Check if elements exist
if (!startButton) console.error("Start button not found in the DOM");
if (!stopButton) console.error("Stop button not found in the DOM");
if (!statusDisplay) console.error("Status display not found in the DOM");
if (!attendanceList) console.error("Attendance list not found in the DOM");

// Event listeners
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded");

    // Re-get elements in case they weren't available earlier
    const startBtn = document.getElementById('startButton');
    const stopBtn = document.getElementById('stopButton');

    if (startBtn) {
        console.log("Adding click listener to start button");
        startBtn.addEventListener('click', startListening);
    } else {
        console.error("Start button not found after DOM loaded");
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', stopListening);
    }
});

// Initialize the model
async function init() {
    console.log("Initializing model...");
    statusDisplay.textContent = "Loading model...";
    statusDisplay.className = "alert alert-info";

    if (typeof speechCommands === 'undefined') {
        console.error('Speech Commands library not loaded');
        statusDisplay.textContent = "Error: Speech Commands library not loaded. Please check your internet connection and refresh.";
        statusDisplay.className = "alert alert-danger";
        return;
    }

    // Fix the URLs - separate model.json and metadata.json
    const baseURL = "https://teachablemachine.withgoogle.com/models/rVWQ-CEJ6/";
    const modelURL = baseURL + "model.json";
    const metadataURL = baseURL + "metadata.json";

    console.log("Model URL:", modelURL);
    console.log("Metadata URL:", metadataURL);

    try {
        console.log("Creating speech commands recognizer...");

        // Load the model and metadata
        const recognizer = speechCommands.create(
            "BROWSER_FFT", // fourier transform type
            undefined, // speech commands vocabulary feature
            modelURL,
            metadataURL
        );

        console.log("Ensuring model is loaded...");
        // Check if model is loaded
        await recognizer.ensureModelLoaded();
        console.log("Model loaded successfully!");

        // Store the model in the global variable
        model = recognizer;

        // Get the total number of classes
        maxPredictions = model.wordLabels().length;
        console.log(`Model has ${maxPredictions} classes:`, model.wordLabels());

        statusDisplay.textContent = "Model loaded. Ready to detect sounds.";
        statusDisplay.className = "alert alert-success";

        // Enable the start button
        if (startButton) {
            startButton.disabled = false;
        }
    } catch (error) {
        console.error('Error loading model:', error);
        statusDisplay.textContent = "Error loading model. Please refresh the page.";
        statusDisplay.className = "alert alert-danger";
    }
}

// Start listening for sounds
async function startListening() {
    console.log("Start button clicked");

    if (!model) {
        console.log("Model not loaded, initializing...");
        await init();
    }

    if (!model) {
        console.error("Failed to initialize model");
        return;
    }

    if (isListening) {
        console.log("Already listening, ignoring click");
        return;
    }

    isListening = true;
    startButton.disabled = true;
    stopButton.disabled = false;

    statusDisplay.textContent = "Listening for sounds...";
    statusDisplay.className = "alert alert-primary";

    console.log("Starting audio classification...");
    // Start the audio classification loop
    classifyAudio();
}

// Stop listening for sounds
function stopListening() {
    console.log("Stop button clicked");
    isListening = false;
    startButton.disabled = false;
    stopButton.disabled = true;

    statusDisplay.textContent = "Stopped listening.";
    statusDisplay.className = "alert alert-secondary";

    if (model) {
        console.log("Stopping model listening");
        model.stopListening();
    }
}

// Continuously classify audio
async function classifyAudio() {
    if (!isListening) return;

    try {
        console.log("Starting to listen for audio...");
        // Get the prediction from the model
        await model.listen(result => {
            // Get the top prediction
            const scores = result.scores;

            // Find the class with the highest score
            let maxScore = 0;
            let maxScoreIndex = -1;

            for (let i = 0; i < scores.length; i++) {
                if (scores[i] > maxScore) {
                    maxScore = scores[i];
                    maxScoreIndex = i;
                }
            }

            // Get the label for the top prediction
            const topPredictionLabel = model.wordLabels()[maxScoreIndex];

            console.log(`Detected: ${topPredictionLabel} (${maxScore.toFixed(2)})`);

            // Check if the confidence is high enough
            if (maxScore > 0.8) {
                const soundLabel = topPredictionLabel;

                // If this is a student sound (not background noise)
                if (soundLabel !== "Background Noise") {
                    statusDisplay.textContent = `Detected: ${soundLabel}`;
                    statusDisplay.className = "alert alert-success";

                    // Mark attendance for this student
                    markAttendance(soundLabel);
                }
            }
        }, {
            includeSpectrogram: false,
            probabilityThreshold: 0.75,
            invokeCallbackOnNoiseAndUnknown: false,
            overlapFactor: 0.5
        });

        // Continue the classification loop
        if (!isListening) {
            model.stopListening();
        }
    } catch (error) {
        console.error('Error during audio classification:', error);
        statusDisplay.textContent = "Error detecting sound.";
        statusDisplay.className = "alert alert-danger";

        // Try to restart after a delay
        if (isListening) {
            setTimeout(classifyAudio, 2000);
        }
    }
}

// Mark attendance for a student
async function markAttendance(soundLabel) {
    // Check if we've already marked this student recently
    if (attendanceRecords[soundLabel] &&
        (Date.now() - attendanceRecords[soundLabel].timestamp) < 60000) {
        // Don't mark attendance again within 1 minute
        return;
    }

    try {
        // This would be a call to your backend in a real implementation
        // For now, we'll simulate it
        const studentId = soundLabel; // In a real system, you'd map the sound label to a student ID

        // Record the attendance locally
        const now = new Date();
        attendanceRecords[soundLabel] = {
            timestamp: Date.now(),
            time: now.toLocaleTimeString()
        };

        // Add to the attendance list in the UI
        addAttendanceRecord(studentId, now.toLocaleTimeString());

        // Send to the server
        await sendAttendanceToServer(studentId);

    } catch (error) {
        console.error('Error marking attendance:', error);
    }
}

// Add an attendance record to the UI
function addAttendanceRecord(studentId, time) {
    const row = document.createElement('tr');

    row.innerHTML = `
        <td>${studentId}</td>
        <td>Student Name</td>
        <td><span class="badge bg-success">Present</span></td>
        <td>${time}</td>
    `;

    if (attendanceList) {
        // Add at the top of the list
        if (attendanceList.firstChild) {
            attendanceList.insertBefore(row, attendanceList.firstChild);
        } else {
            attendanceList.appendChild(row);
        }
    }
}

// Send attendance data to the server
async function sendAttendanceToServer(studentId) {
    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                present: true
            })
        });

        const data = await response.json();

        if (!data.success) {
            console.error('Server error marking attendance:', data.error);
        }
    } catch (error) {
        console.error('Error sending attendance to server:', error);
    }
}

// Initialize the page
window.onload = function () {
    // We'll initialize the model when the user clicks the start button
    if (startButton) {
        startButton.disabled = false;
    }
};