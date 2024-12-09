// src/frontend/static/main.js
document.addEventListener("DOMContentLoaded", () => {
    const userPrompt = document.getElementById('user-prompt');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    loadMessages();

    sendBtn.addEventListener('click', async () => {
        const goal = userPrompt.value.trim();
        if (!goal) return;
        userPrompt.value = "Running...";
        sendBtn.disabled = true;

        const resp = await fetch("/api/new_goal", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({goal})
        });

        if (resp.ok) {
            userPrompt.value = "";
            sendBtn.disabled = false;
            await loadMessages();
        } else {
            userPrompt.value = "Error.";
            sendBtn.disabled = false;
        }
    });

    async function loadMessages() {
        const resp = await fetch('/api/messages');
        if (!resp.ok) {
            chatMessages.textContent = "Error loading messages.";
            return;
        }

        const data = await resp.json();
        const msgs = data.messages;

        chatMessages.innerHTML = "";

        const userGoals = msgs.filter(m => m.tags.includes("user_goal"));
        const finalResults = msgs.filter(m => m.tags.includes("final_result"));
        const summaries = msgs.filter(m => m.tags.includes("summary_message"));

        // For each user goal, find the final_result after it
        // Show: user goal, then a line "A team of agents...", then final_result
        // at the end show summary_message
        for (let g of userGoals) {
            addMessageBlockText(g.sender, g.content); // user goal text

            // Add team-of-agents line
            addMessageBlockText("System", "A team of agents are thinking and collaborating to find your answer...");

            // find final_result after this goal
            const fr = finalResults.filter(r => r.timestamp > g.timestamp);
            if (fr.length > 0) {
                const latestFR = fr[fr.length - 1];
                addMessageBlockHTML(latestFR.sender, latestFR.content);
            }
        }

        // show the latest summary at the very end
        if (summaries.length > 0) {
            const latestSummary = summaries[summaries.length - 1];
            addMessageBlockText("Summary", latestSummary.content);
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addMessageBlockText(senderName, textContent) {
        const div = document.createElement('div');
        div.classList.add('message-block');

        const sender = document.createElement('div');
        sender.classList.add('sender');
        sender.textContent = senderName;

        const content = document.createElement('div');
        content.classList.add('content');
        content.textContent = textContent;

        div.appendChild(sender);
        div.appendChild(content);
        chatMessages.appendChild(div);
    }

    function addMessageBlockHTML(senderName, htmlContent) {
        const div = document.createElement('div');
        div.classList.add('message-block');

        const sender = document.createElement('div');
        sender.classList.add('sender');
        sender.textContent = senderName;

        const content = document.createElement('div');
        content.classList.add('content');
        content.innerHTML = htmlContent; // set HTML for final_result

        div.appendChild(sender);
        div.appendChild(content);
        chatMessages.appendChild(div);
    }
});
