const { createApp } = Vue;

createApp({
  data() {
    return {
      view: "consult", // consult | manage
      // ---- 智能咨询（无状态，前端维护历史）----
      consult: [],
      consultInput: "",
      consulting: false,
      suggestions: [
        "血压总是偏高，日常要注意什么？",
        "老人晚上睡不好，怎么改善？",
        "糖尿病老人饮食有哪些禁忌？",
        "如何预防老人跌倒？",
        "记性越来越差，需要看医生吗？",
      ],
      // ---- 健康管理 ----
      elders: [],
      current: null,
      form: { name: "", gender: "男", age: 70, medical_history: "", medications: "" },
      vitals: [],
      vital: {},
      reports: [],
      assessment: null,
      findings: {},
      assessing: false,
      messages: [],
      chatInput: "",
      chatting: false,
      // ---- 通用 ----
      toast: "",
      recognition: null,
      recording: false,
      voiceSupported: false,
    };
  },
  async mounted() {
    await this.loadElders();
    this.setupVoice();
  },
  methods: {
    notify(msg) { this.toast = msg; setTimeout(() => (this.toast = ""), 2400); },
    // 轻量、安全的 Markdown 渲染（先转义，再处理标题/加粗/分隔），用于智能体回复
    md(text) {
      const esc = (text || "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return esc
        .replace(/^#{1,6}\s*(.+)$/gm, '<strong class="md-h">$1</strong>')
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/^\s*[-•]\s+/gm, "· ");
    },
    fmt(s) { return s ? new Date(s).toLocaleString("zh-CN", { hour12: false }).slice(5, 16) : "-"; },
    async api(path, opts = {}) {
      const res = await fetch(path, opts);
      if (!res.ok) {
        let detail = res.statusText;
        try { detail = (await res.json()).detail || detail; } catch (e) {}
        throw new Error(detail);
      }
      return res.status === 204 ? null : res.json();
    },

    // ---------- 智能咨询 ----------
    askSuggestion(q) { this.consultInput = q; this.sendConsult(); },
    async sendConsult() {
      const text = this.consultInput.trim();
      if (!text || this.consulting) return;
      this.consult.push({ role: "user", content: text });
      this.consultInput = "";
      this.consulting = true;
      this.scroll("stream");
      try {
        const history = this.consult.slice(0, -1).map((m) => ({ role: m.role, content: m.content }));
        const r = await this.api("/api/consult", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, history }),
        });
        this.consult.push({ role: "assistant", content: r.content });
      } catch (e) {
        this.consult.push({ role: "assistant", content: "抱歉，暂时无法回应：" + e.message });
      }
      this.consulting = false;
      this.scroll("stream");
    },

    // ---------- 老人档案 ----------
    async loadElders() { this.elders = await this.api("/api/elders"); },
    async createElder() {
      try {
        const e = await this.api("/api/elders", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.form),
        });
        this.form.name = ""; this.form.medical_history = ""; this.form.medications = "";
        await this.loadElders();
        this.selectElder(e);
        this.notify("档案已创建");
      } catch (e) { this.notify("创建失败：" + e.message); }
    },
    async selectElder(e) {
      this.current = e;
      this.assessment = null; this.findings = {};
      await Promise.all([this.loadVitals(), this.loadReports(), this.loadChat()]);
    },
    async loadVitals() { this.vitals = await this.api(`/api/elders/${this.current.id}/vitals`); },
    async addVital() {
      try {
        await this.api(`/api/elders/${this.current.id}/vitals`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.vital),
        });
        this.vital = {};
        await this.loadVitals();
        this.notify("已录入");
      } catch (e) { this.notify("录入失败：" + e.message); }
    },
    async loadReports() { this.reports = await this.api(`/api/elders/${this.current.id}/reports`); },
    async uploadReport(ev) {
      const file = ev.target.files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append("file", file);
      this.notify("解析报告中…");
      try {
        await this.api(`/api/elders/${this.current.id}/reports`, { method: "POST", body: fd });
        await this.loadReports();
        this.notify("报告已解析");
      } catch (e) { this.notify("上传失败：" + e.message); }
      this.$refs.fileInput.value = "";
    },
    async runAssessment() {
      this.assessing = true;
      try {
        const a = await this.api(`/api/elders/${this.current.id}/assessment`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        this.assessment = a;
        try { this.findings = JSON.parse(a.findings_json); } catch (e) { this.findings = {}; }
      } catch (e) { this.notify("评估失败：" + e.message); }
      this.assessing = false;
    },
    async loadChat() { this.messages = await this.api(`/api/elders/${this.current.id}/chat`); },
    async sendChat() {
      const text = this.chatInput.trim();
      if (!text || this.chatting) return;
      this.chatting = true;
      this.messages.push({ id: "tmp", role: "user", content: text });
      this.chatInput = "";
      this.scroll("elderStream");
      try {
        await this.api(`/api/elders/${this.current.id}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        await this.loadChat();
        this.scroll("elderStream");
      } catch (e) { this.notify("发送失败：" + e.message); }
      this.chatting = false;
    },

    // ---------- 通用 ----------
    scroll(ref) {
      this.$nextTick(() => {
        const b = this.$refs[ref];
        if (b) b.scrollTop = b.scrollHeight;
      });
    },
    setupVoice() {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) { this.voiceSupported = false; return; }
      this.voiceSupported = true;
      const rec = new SR();
      rec.lang = "zh-CN";
      rec.interimResults = false;
      rec.onresult = (ev) => { this.consultInput = ev.results[0][0].transcript; };
      rec.onend = () => { this.recording = false; };
      rec.onerror = () => { this.recording = false; this.notify("语音识别失败"); };
      this.recognition = rec;
    },
    toggleVoice() {
      if (!this.voiceSupported) { this.notify("当前浏览器不支持语音输入，请手动输入"); return; }
      if (this.recording) { this.recognition.stop(); this.recording = false; }
      else { this.recognition.start(); this.recording = true; }
    },
  },
}).mount("#app");
