// static/script.js
document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("send-btn");
    const userInput = document.getElementById("user-input");
    const storyBox = document.getElementById("story-box");
    const progressBar = document.getElementById("progress-bar");
    const clueSpan = document.getElementById("current-clue");
  
    function appendMessage(text, cls="npc") {
      const p = document.createElement("div");
      p.className = `msg ${cls}`;
      p.innerText = text;
      storyBox.appendChild(p);
      storyBox.scrollTop = storyBox.scrollHeight;
    }
  
    // small helper to show subtle system messages
    function appendSmall(text) {
      const p = document.createElement("div");
      p.className = `msg small`;
      p.innerText = text;
      storyBox.appendChild(p);
      storyBox.scrollTop = storyBox.scrollHeight;
    }
  
    async function sendInput() {
      const input = userInput.value.trim();
      if (!input) return;
      appendMessage(input, "player");
      userInput.value = "";
      userInput.disabled = true;
      sendBtn.disabled = true;
  
      // nice typing simulation before response:
      const typing = document.createElement("div");
      typing.className = "msg npc";
      typing.innerText = "...";
      storyBox.appendChild(typing);
      storyBox.scrollTop = storyBox.scrollHeight;
  
      try {
        const resp = await fetch("/play", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input })
        });
        const data = await resp.json();
  
        // remove typing indicator
        typing.remove();
  
        // show NPC response
        appendMessage(data.message, "npc");
  
        // progress bar
        if (typeof data.progress === "number") {
          progressBar.style.width = data.progress + "%";
        }
  
        // Update clue only when stage passed
        if (data.passed) {
          if (data.clue) {
            clueSpan.innerText = data.clue;
            appendSmall("Clue updated.");
          } else {
            clueSpan.innerText = "(no clue)";
          }
        } else {
          // keep clue unchanged — no extra clue message shown
        }
  
        if (data.completed) {
          appendSmall("Story completed.");
          userInput.disabled = true;
          sendBtn.disabled = true;
        }
  
      } catch (err) {
        typing.remove();
        appendMessage("Network error. Check console for details.", "npc");
        console.error(err);
      } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
      }
    }
  
    sendBtn.addEventListener("click", sendInput);
    userInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendInput();
    });
  });
  