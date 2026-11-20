// =====================================
// BIRTHDAY BUDDY - VERSION 3
// Dialogue State, Context and Clarification
// =====================================


// Get HTML elements
const chatBox = document.getElementById("chat-box");

const userInput = document.getElementById("user-input");

const sendButton = document.getElementById("send-btn");

const resetButton = document.getElementById("reset-btn");


// =====================================
// GET CURRENT TIME
// =====================================

function getTime() {

    const now = new Date();

    return now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });

}


// =====================================
// ADD MESSAGE TO CHAT
// =====================================

function addMessage(message, sender) {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("message");

    if (sender === "user") {

        messageDiv.classList.add("user-message");

    } else {

        messageDiv.classList.add("bot-message");

    }


    // Avatar
    const avatar = document.createElement("div");

    avatar.classList.add("avatar");

    avatar.textContent = sender === "user" ? "😊" : "🎂";


    // Message content
    const content = document.createElement("div");

    content.classList.add("message-content");


    // Message text
    const paragraph = document.createElement("p");

    paragraph.textContent = message;


    // Time
    const time = document.createElement("span");

    time.classList.add("message-time");

    time.textContent = getTime();


    // Add elements
    content.appendChild(paragraph);

    content.appendChild(time);

    messageDiv.appendChild(avatar);

    messageDiv.appendChild(content);


    // Display message
    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;

}


// =====================================
// SHOW TYPING INDICATOR
// =====================================

function showTyping() {

    const typingDiv = document.createElement("div");

    typingDiv.id = "typing-indicator";

    typingDiv.classList.add("message", "bot-message");

    typingDiv.innerHTML = `
        <div class="avatar">🎂</div>

        <div class="message-content">
            <p>Birthday Buddy is typing... 💭</p>
        </div>
    `;

    chatBox.appendChild(typingDiv);

    chatBox.scrollTop = chatBox.scrollHeight;

}


// =====================================
// REMOVE TYPING INDICATOR
// =====================================

function removeTyping() {

    const typing = document.getElementById("typing-indicator");

    if (typing) {

        typing.remove();

    }

}


// =====================================
// SEND MESSAGE
// =====================================

async function sendMessage() {

    const message = userInput.value.trim();


    // Check empty message
    if (message === "") {

        return;

    }


    // Display user message
    addMessage(message, "user");


    // Clear input
    userInput.value = "";


    // Disable send button
    sendButton.disabled = true;

    showTyping();


    try {

        // Send message to Flask backend
        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });


        if (!response.ok) {

            throw new Error("Server error");

        }


        const data = await response.json();


        // Remove typing animation
        removeTyping();


        // Get assistant response
        const reply =
            data.reply ||
            data.answer ||
            data.response ||
            "Sorry! I couldn't understand that. 💗";


        // Display assistant response
        addMessage(reply, "bot");


    } catch (error) {

        removeTyping();

        console.error("Error:", error);

        addMessage(
            "Oops! Something went wrong. Please check whether the server is running. 💔",
            "bot"
        );

    }


    // Enable send button
    sendButton.disabled = false;

    userInput.focus();

}


// =====================================
// QUICK QUESTIONS
// =====================================

function sendQuickMessage(message) {

    userInput.value = message;

    sendMessage();

}


// =====================================
// ENTER KEY SUPPORT
// =====================================

userInput.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {

        sendMessage();

    }

});


// =====================================
// RESET CONVERSATION - VERSION 3
// =====================================

async function resetConversation() {

    const confirmation = confirm(
        "Are you sure you want to reset this conversation? 💗"
    );


    if (!confirmation) {

        return;

    }


    try {

        // Call Flask reset endpoint
        const response = await fetch("/reset", {

            method: "POST"

        });


        if (!response.ok) {

            throw new Error("Unable to reset conversation");

        }


        const data = await response.json();


        // Clear previous chat messages
        chatBox.innerHTML = "";


        // Display fresh welcome message
        addMessage(
            "Your conversation has been reset! 🎉 Let's start fresh. What birthday would you like to know about? 💗",
            "bot"
        );


        // Clear input
        userInput.value = "";

        userInput.focus();


    } catch (error) {

        console.error("Reset error:", error);

        alert("Unable to reset conversation. Please try again.");

    }

}