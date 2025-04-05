/**
 * Minerva Chat Integration
 * Embeds the chat functionality directly into the Minerva UI
 */

document.addEventListener("DOMContentLoaded", () => {
    const inputField = document.getElementById("chat-input");
    const sendButton = document.getElementById("chat-send-button");

    if (!inputField || !sendButton) {
        console.error("Chat input or send button not found!");
        return;
    }

    function sendMessage() {
        const message = inputField.value.trim();
        if (message === "") return;
        sendMessageToAPI(message);
        inputField.value = ""; // Clear input after sending
    }

    inputField.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener("click", sendMessage);
});
