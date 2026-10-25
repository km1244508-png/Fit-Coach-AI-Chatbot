import Spinner from "../ui/Spinner.jsx";

export default function SubmitButton({ loading, children, loadingText }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="flex w-full items-center justify-center gap-2 rounded-xl bg-linear-to-r from-emerald-400 to-cyan-400 px-4 py-3 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-500/25 transition hover:brightness-110 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-emerald-300 disabled:cursor-not-allowed disabled:opacity-70"
    >
      {loading && <Spinner size={17} />}
      {loading ? loadingText : children}
    </button>
  );
}
