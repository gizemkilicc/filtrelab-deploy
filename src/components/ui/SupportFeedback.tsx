import { Headphones, Mail, MessageSquareText, Send } from "lucide-react";

export function SupportFeedback() {
  return (
    <section className="w-full border-t border-slate-200/70 bg-white/70 px-6 py-16">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-[0_14px_34px_rgba(15,23,42,0.18)]">
            <Headphones className="h-5 w-5" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-950 md:text-4xl">
            Support & Feedback
          </h2>
          <p className="mt-4 max-w-xl text-[15px] leading-7 text-slate-600">
            FiltreLAB deneyimini geliştirmek için sorunları, önerileri ve ürün analiz
            taleplerini buradan bize iletebilirsiniz.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_32px_rgba(15,23,42,0.05)]">
              <Mail className="mb-3 h-5 w-5 text-purple-600" />
              <h3 className="font-semibold text-slate-950">Destek</h3>
              <p className="mt-1 text-sm text-slate-500">support@filtrelab.com</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_32px_rgba(15,23,42,0.05)]">
              <MessageSquareText className="mb-3 h-5 w-5 text-cyan-600" />
              <h3 className="font-semibold text-slate-950">Geri Bildirim</h3>
              <p className="mt-1 text-sm text-slate-500">24 saat içinde incelenir</p>
            </div>
          </div>
        </div>

        <form className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_50px_rgba(15,23,42,0.07)] md:p-8">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Adınız</span>
              <input
                type="text"
                placeholder="Ad Soyad"
                className="mt-2 h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-950 outline-none transition focus:border-purple-300 focus:bg-white"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">E-posta</span>
              <input
                type="email"
                placeholder="ornek@mail.com"
                className="mt-2 h-12 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 text-sm text-slate-950 outline-none transition focus:border-purple-300 focus:bg-white"
              />
            </label>
          </div>

          <label className="mt-4 block">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Mesajınız</span>
            <textarea
              rows={5}
              placeholder="Sorunuzu veya önerinizi yazın..."
              className="mt-2 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-950 outline-none transition focus:border-purple-300 focus:bg-white"
            />
          </label>

          <button
            type="button"
            className="mt-5 inline-flex h-12 items-center justify-center gap-2 rounded-full bg-slate-950 px-6 text-sm font-semibold text-white shadow-[0_14px_34px_rgba(15,23,42,0.18)] transition hover:bg-slate-800 active:scale-[0.98]"
          >
            Gönder
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </section>
  );
}
