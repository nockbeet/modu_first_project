// 1. 로그인 화면 이벤트
document.addEventListener("DOMContentLoaded", () => {
    // 로그인 버튼
    const loginBtn = document.getElementById("loginBtn");
    if (loginBtn) {
        loginBtn.addEventListener("click", async () => {
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();

            if (!username || !password) {
                alert("아이디와 비밀번호를 입력해주세요.");
                return;
            }

            try {
                const response = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert(errorData.detail || "로그인 실패");
                    return;
                }

                // 로그인 성공 → 채팅 화면으로 이동
                window.location.href = "/static/chat.html";

            } catch (err) {
                console.error(err);
                alert("서버 오류 발생");
            }
        });
    }

    // 회원가입 화면으로 이동 버튼
    const goRegisterBtn = document.getElementById("goRegisterBtn");
    if (goRegisterBtn) {
        goRegisterBtn.addEventListener("click", () => {
            window.location.href = "/static/register.html";
        });
    }
});


// 2. 회원가입 화면 이벤트
document.addEventListener("DOMContentLoaded", () => {
    // register.html 전용 회원가입 버튼
    const registerBtn = document.getElementById("registerBtn");
    if (registerBtn) {
        registerBtn.addEventListener("click", async () => {
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();
            const passwordConfirm = document.getElementById("passwordConfirm").value.trim();

            // 1️⃣ 빈 칸 체크
            if (!username || !password || !passwordConfirm) {
                alert("모든 입력란을 채워주세요.");
                return;
            }

            // 2️⃣ 비밀번호 일치 체크
            if (password !== passwordConfirm) {
                alert("비밀번호가 일치하지 않습니다.");
                return;
            }

            try {
                const response = await fetch("/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert(errorData.detail || "회원가입 실패");
                    return;
                }

                alert("회원가입 성공! 로그인 화면으로 이동합니다.");
                window.location.href = "/static/login.html";

            } catch (err) {
                console.error(err);
                alert("서버 오류 발생");
            }
        });
    }

    // register.html 전용 로그인 화면 이동 버튼
    const goLoginBtn = document.getElementById("goLoginBtn");
    if (goLoginBtn) {
        goLoginBtn.addEventListener("click", () => {
            window.location.href = "/static/login.html";
        });
    }
});


// 3. 채팅 화면 이벤트
document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chatBox");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const historyBtn = document.getElementById("historyBtn");

    // 말풍선 형태로 메시지 추가
    function appendMessage(sender, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-message ${sender}`;
        msgDiv.textContent = text;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // 스크롤 자동 하단 이동
    }

    // 메시지 전송
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage("user", message);  // 사용자 메시지 화면에 표시
        chatInput.value = "";

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify([{ role: "user", content: message }])
            });

            if (!response.ok) {
                if (response.status === 401) {
                    alert("로그인이 필요합니다.");
                    window.location.href = "/static/login.html";
                    return;
                }
                throw new Error("응답 실패");
            }

            const data = await response.json();
            appendMessage("assistant", data.assistant_reply);  // MovieBot 응답 화면에 표시

        } catch (err) {
            console.error(err);
            appendMessage("assistant", "⚠️ 서버 오류가 발생했습니다.");
        }
    }

    // 전송 버튼 클릭
    if (sendBtn) sendBtn.addEventListener("click", sendMessage);

    // Enter 키 이벤트
    if (chatInput) {
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }

    // 로그아웃 버튼 클릭
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            await fetch("/logout", { method: "POST", credentials: "same-origin" });
            window.location.href = "/static/login.html";
        });
    }

    // 채팅 기록 버튼 클릭
    if (historyBtn) {
        historyBtn.addEventListener("click", () => {
            window.location.href = "/static/history.html";
        });
    }
});

// 4. 채팅 기록 화면 이벤트
// -----------------------------
// 채팅 기록 화면 기능
// -----------------------------
function loadChatHistory() {
    const chatHistoryDiv = document.getElementById('chatHistory');
    if (!chatHistoryDiv) return; // 요소가 없으면 실행하지 않음

    fetch('/chat/history')
        .then(res => {
            if (!res.ok) throw new Error('채팅 기록을 가져올 수 없습니다.');
            return res.json();
        })
        .then(data => {
            chatHistoryDiv.innerHTML = '';

            let conversationDiv = null;

            data.history.forEach(msg => {
                // user 메시지 나오면 새 conversation div 생성
                if (msg.role === 'user') {
                    conversationDiv = document.createElement('div');
                    conversationDiv.classList.add('conversation');
                    chatHistoryDiv.appendChild(conversationDiv);
                }

                if (!conversationDiv) return;

                const messageDiv = document.createElement('div');
                messageDiv.classList.add('chat-message');
                messageDiv.classList.add(msg.role === 'assistant' ? 'assistant' : 'user');
                messageDiv.textContent = msg.content;

                conversationDiv.appendChild(messageDiv);
            });

            // 스크롤 맨 아래로 이동
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        })
        .catch(err => alert(err.message));
}

// '채팅으로 돌아가기' 버튼 이벤트
const backBtn = document.getElementById('backToChatBtn');
if (backBtn) {
    backBtn.addEventListener('click', () => {
        window.location.href = '/static/chat.html';
    });
}

// 페이지 로드 시 history 화면이면 실행
window.addEventListener('DOMContentLoaded', () => {
    const chatHistoryDiv = document.getElementById('chatHistory');
    if (chatHistoryDiv) {
        loadChatHistory();
    }
});
