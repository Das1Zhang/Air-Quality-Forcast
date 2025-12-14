const API_BASE = ""; // 使用相对路径，跟随当前页面所在的域名和端口

const cities = [
    "武汉市",
    "黄石市",
    "十堰市",
    "宜昌市",
    "襄阳市",
    "鄂州市",
    "荆门市",
    "孝感市",
    "荆州市",
    "黄冈市",
    "咸宁市",
    "随州市",
    "恩施土家族苗族自治州",
    "仙桃市",
    "潜江市",
    "天门市",
    "神农架林区",
];

const stageList = [
    { id: "stage1", title: "阶段 1", desc: "数据整合" },
    { id: "stage2", title: "阶段 2", desc: "探索性数据分析" },
    { id: "stage3", title: "阶段 3", desc: "特征工程" },
    { id: "stage4", title: "阶段 4", desc: "模型训练" },
    { id: "stage5", title: "阶段 5", desc: "评估与预测" },
    { id: "stage6", title: "阶段 6", desc: "可视化展示" },
];

const stagingFiles = [];
const citySelect = document.getElementById("citySelect");
const stagingList = document.getElementById("stagingList");
const stagingHint = document.getElementById("stagingHint");
const consoleBox = document.getElementById("console");

function initCitySelect() {
    cities.forEach((city) => {
        const option = document.createElement("option");
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
    });
}

function updateStagingView() {
    stagingList.innerHTML = "";
    if (!stagingFiles.length) {
        stagingHint.style.display = "block";
        return;
    }
    stagingHint.style.display = "none";
    stagingFiles.forEach((file, index) => {
        const li = document.createElement("li");
        li.className = "staging__item";
        li.innerHTML = `
      <div>
        <span>${file.name}</span>
        <p class="muted">${(file.size / 1024).toFixed(1)} KB</p>
      </div>
      <button class="button ghost" data-remove="${index}">移除</button>
    `;
        stagingList.appendChild(li);
    });
}

function handleFiles(files) {
    const fileArray = Array.from(files);
    if (!fileArray.length) return;

    // 只保留一个文件（新文件覆盖旧文件）
    stagingFiles.length = 0;
    stagingFiles.push(fileArray[0]);
    updateStagingView();
}

function setStageStatus(stageId, status, text) {
    const card = document.querySelector(`.stage-card[data-stage="${stageId}"]`);
    if (!card) return;
    const label = card.querySelector(".stage-status");
    label.className = `stage-status status-${status}`;
    label.textContent = text;
}

function appendConsole(message) {
    const line = document.createElement("p");
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    consoleBox.appendChild(line);
    consoleBox.scrollTop = consoleBox.scrollHeight;
}

document.getElementById("dropZone").addEventListener("click", () => {
    document.getElementById("fileInput").click();
});

document
    .getElementById("fileInput")
    .addEventListener("change", (e) => handleFiles(e.target.files));

document
    .getElementById("dropZone")
    .addEventListener("dragover", (e) => e.preventDefault());

document
    .getElementById("dropZone")
    .addEventListener("drop", (e) => {
        e.preventDefault();
        handleFiles(e.dataTransfer.files);
    });

document
    .getElementById("clearStaging")
    .addEventListener("click", () => {
        stagingFiles.length = 0;
        updateStagingView();
        appendConsole("已清空暂存区文件。");
    });

stagingList.addEventListener("click", (e) => {
    if (e.target.dataset.remove !== undefined) {
        stagingFiles.splice(Number(e.target.dataset.remove), 1);
        updateStagingView();
    }
});

document.getElementById("uploadBtn").addEventListener("click", async () => {
    if (!stagingFiles.length) {
        alert("请先选择一个数据文件！");
        return;
    }
    const city = citySelect.value;
    if (!city) {
        alert("请先选择一个市区！");
        return;
    }

    appendConsole(`开始上传到暂存区：城市 = ${city} ...`);

    const formData = new FormData();
    // 只上传一个文件
    formData.append("file", stagingFiles[0]);
    formData.append("city", city);

    try {
        const resp = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: formData });
        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }
        appendConsole(`上传完成：${city}。`);
        // 上传成功后清空暂存区，避免误用旧文件
        stagingFiles.length = 0;
        updateStagingView();
    } catch (err) {
        appendConsole(`上传失败：${err}`);
    }
});

document.getElementById("trainBtn").addEventListener("click", async () => {
    appendConsole("启动训练与预测流程...");
    stageList.forEach((stage) =>
        setStageStatus(stage.id, "running", "执行中")
    );
    try {
        await fetch(`${API_BASE}/api/run_pipeline`, { method: "POST" });
        stageList.forEach((stage) =>
            setStageStatus(stage.id, "success", "完成")
        );
        appendConsole("所有阶段已完成。");
    } catch (err) {
        stageList.forEach((stage) =>
            setStageStatus(stage.id, "error", "失败")
        );
        appendConsole(`流程失败：${err}`);
    }
});

document
    .getElementById("refreshStages")
    .addEventListener("click", async () => {
        appendConsole("刷新阶段状态...");
        try {
            const res = await fetch(`${API_BASE}/api/status`);
            const status = await res.json();

            stageList.forEach(({ id }) => {
                try {
                    const state = status[id] || { status: "idle", text: "待开始" };
                    setStageStatus(id, state.status, state.text);
                    const output = document.getElementById(`${id}-output`);
                    if (!output) return;

                    const out = state.output;
                    if (Array.isArray(out) && out.length > 0) {
                        // 多个输出：渲染为多个链接
                        const links = out
                            .map((item) => {
                                if (!item || !item.path) return "";
                                const rawPath = item.path;
                                const url = rawPath.startsWith("/")
                                    ? rawPath
                                    : `/${rawPath}`;
                                const label = item.label || "查看输出";
                                return `<a href="${url}" target="_blank">${label}</a>`;
                            })
                            .filter(Boolean)
                            .join(" | ");
                        output.innerHTML = links || '<p class="placeholder">暂无输出</p>';
                    } else if (typeof out === "string" && out) {
                        // 单个输出：兼容之前的字符串形式
                        const url = out.startsWith("/") ? out : `/${out}`;
                        output.innerHTML = `<a href="${url}" target="_blank">查看输出</a>`;
                    } else {
                        output.innerHTML = '<p class="placeholder">暂无输出</p>';
                    }
                } catch (err) {
                    console.error(`渲染 ${id} 输出失败`, err);
                }
            });
        } catch (err) {
            console.error("刷新阶段状态失败", err);
            appendConsole(`刷新状态失败：${err}`);
        }
    });

const btnWorkflow = document.getElementById("btnWorkflow");
const btnLSTM = document.getElementById("btnLSTM");
const overlay = document.getElementById("diagramOverlay");
const overlayImg = document.getElementById("diagramImage");
const overlayClose = document.getElementById("diagramClose");
const overlayBackdrop = document.getElementById("diagramOverlayBackdrop");

function showDiagram(url, alt) {
    if (!overlay || !overlayImg) return;
    overlayImg.src = url;
    overlayImg.alt = alt;
    overlay.classList.add("is-visible");
}

function hideDiagram() {
    if (!overlay) return;
    overlay.classList.remove("is-visible");
}

if (btnWorkflow) {
    btnWorkflow.addEventListener("click", () => {
        showDiagram(
            "https://132-1331126615.cos.ap-guangzhou.myqcloud.com/workflow.png",
            "项目工作流程图"
        );
    });
}

if (btnLSTM) {
    btnLSTM.addEventListener("click", () => {
        showDiagram(
            "https://132-1331126615.cos.ap-guangzhou.myqcloud.com/LSTM.png",
            "LSTM 模型原理图"
        );
    });
}

if (overlayClose) {
    overlayClose.addEventListener("click", hideDiagram);
}

if (overlayBackdrop) {
    overlayBackdrop.addEventListener("click", hideDiagram);
}

initCitySelect();
updateStagingView();