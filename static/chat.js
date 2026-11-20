const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");

function getTime() {
    return new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}


function addMessage(message, sender) {

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");

    const content = document.createElement("div");
    content.classList.add("message-content");

    const paragraph = document.createElement("p");

    // Preserve line breaks and display text safely.
    paragraph.textContent = message;

    const time = document.createElement("span");
    time.classList.add("time");
    time.textContent = getTime();

    content.appendChild(paragraph);
    content.appendChild(time);

    if (sender === "user") {

        messageDiv.classList.add("user-message");
        messageDiv.appendChild(content);

    } else {

        messageDiv.classList.add("bot-message");

        const avatar = document.createElement("div");
        avatar.classList.add("avatar");
        avatar.textContent = "🎂";

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
    }

    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}


function showTyping() {

    const typing = document.createElement("div");
    typing.classList.add("typing");
    typing.id = "typing";

    typing.textContent = "🎀 Birthday Buddy is typing...";

    chatBox.appendChild(typing);

    chatBox.scrollTop = chatBox.scrollHeight;
}


function removeTyping() {

    const typing = document.getElementById("typing");

    if (typing) {
        typing.remove();
    }
}


async function sendMessage() {

    const message = userInput.value.trim();

    if (message === "") {
        return;
    }

    addMessage(message, "user");

    userInput.value = "";

    showTyping();

    try {

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

        removeTyping();

        const reply =
            data.reply ||
            data.response ||
            data.answer ||
            "Sorry! I couldn't understand that. 💗";

        addMessage(reply, "bot");

    }

    catch (error) {

        removeTyping();

        addMessage(
            "Oops! Something went wrong. Please try again! 💕",
            "bot"
        );

        console.error(error);
    }

}


function sendQuickMessage(message) {

    userInput.value = message;

    sendMessage();

}


// Press Enter to send message

userInput.addEventListener("keypress", function(event) {

    if (event.key === "Enter") {
        sendMessage();
    }

});