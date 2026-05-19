import { Mail, MessageSquareText, Send } from "lucide-react";

export function SupportFeedback() {
  const labelClass = "block fl-mono text-[10px] uppercase tracking-[0.16em] text-[var(--ink-30)] mb-2";

  return (
    <section className="w-full border-t border-[var(--ink-70)] px-6 py-20">
      <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="fl-kicker">DESTEK & GERİ BİLDİRİM</p>
          <h2 className="fl-serif mt-5 text-[40px] leading-[1.05] text-[var(--paper)] md:text-[52px]">
            Sorular ve öneriler
          </h2>
          <p className="fl-sans mt-4 max-w-xl text-[15px] leading-relaxed text-[var(--ink-30)]">
            FiltreLAB deneyimini geliştirmek için sorunları, önerileri ve ürün analiz
            taleplerini buradan bize iletebilirsiniz.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            <div className="fl-card p-5">
              <Mail className="mb-3 h-5 w-5 text-[var(--brass)]" />
              <h3 className="fl-serif text-[18px] text-[var(--paper)]">Destek</h3>
              <p className="fl-mono mt-1 text-[11px] text-[var(--ink-30)]">support@filtrelab.com</p>
            </div>
            <div className="fl-card p-5">
              <MessageSquareText className="mb-3 h-5 w-5 text-[var(--brass)]" />
              <h3 className="fl-serif text-[18px] text-[var(--paper)]">Geri Bildirim</h3>
              <p className="fl-mono mt-1 text-[11px] text-[var(--ink-30)]">24 saat içinde incelenir</p>
            </div>
          </div>
        </div>

        <form className="fl-card p-7 md:p-9">
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block">
              <span className={labelClass}>Adınız</span>
              <input type="text" placeholder="Ad Soyad" className="fl-input" />
            </label>
            <label className="block">
              <span className={labelClass}>E-posta</span>
              <input type="email" placeholder="ornek@mail.com" className="fl-input" />
            </label>
          </div>

          <label className="mt-5 block">
            <span className={labelClass}>Mesajınız</span>
            <textarea
              rows={5}
              placeholder="Sorunuzu veya önerinizi yazın..."
              className="fl-input resize-none"
            />
          </label>

          <button type="button" className="fl-btn fl-btn-primary mt-6">
            Gönder
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </section>
  );
}
