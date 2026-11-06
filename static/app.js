const e = document.querySelector("#profile"),
    m = document.querySelector("#msg"),
    r = document.querySelector("#results");

document.querySelector("#copy").onclick = async () => {
    try {
        await navigator.clipboard.writeText(e.value);
        m.textContent = "Konfigurasi berhasil disalin."
    } catch {
        m.textContent = "Belum ada konfigurasi atau penyalinan tidak tersedia."
    }
};

document.querySelector("#reset").onclick = () => {
    if (!e.value || confirm("Hapus seluruh isi editor?")) {
        e.value = "";
        r.hidden = true;
        m.textContent = ""
    }
};

e.onkeydown = x => {
    if (x.key === "Tab") {
        x.preventDefault();
        e.setRangeText("    ", e.selectionStart, e.selectionEnd, "end")
    }
};

document.querySelector("#validate").onclick = async () => {
    m.textContent = "";
    if (!e.value.trim()) {
        m.textContent = "Isi konfigurasi profil sebelum validasi.";
        return
    }

    let b = document.querySelector("#validate");
    b.disabled = true;
    try {
        let q = await fetch("/api/challenges/secure-file-manager/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ profile: e.value })
            }),
            d = await q.json();
        if (!q.ok) throw Error(d.error);
        r.hidden = false;
        document.querySelector("#title").textContent = d.ok
            ? "Semua pemeriksaan lulus"
            : "Masih ada pemeriksaan yang perlu diperbaiki";
        document.querySelector("#score").textContent = d.score + " / 100";
        let c = document.querySelector("#checks");
        c.replaceChildren();
        for (let x of d.checks) {
            let z = document.createElement("div");
            z.className = "check " + (x.passed ? "good" : "bad");
            z.textContent =
                (x.passed ? "✓ " : "! ") +
                x.label +
                (x.passed ? "" : " — " + (x.message || "Belum lulus"));
            c.append(z)
        }
        let f = document.querySelector("#flag");
        f.hidden = !d.flag;
        f.textContent = d.flag || "";
        if (d.message) m.textContent = d.message;
        r.scrollIntoView({ behavior: "smooth" })
    } catch (x) {
        m.textContent = x.message || "Layanan validator tidak tersedia."
    } finally {
        b.disabled = false
    }
};