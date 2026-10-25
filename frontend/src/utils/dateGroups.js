// Sidebar date clusters are DERIVED from last_message_at on every render (never hard-coded).
// Timezone assumption: the browser's timezone (Intl). Falls back to UTC if unavailable.
export const GROUP_ORDER = ["Today", "Yesterday", "Previous 7 Days", "Older"];

export function userTimeZone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

// Calendar-day index of an instant in a given timezone (DST-safe: compares dates, not 24h blocks).
function dayIndex(date, timeZone) {
  const parts = new Intl.DateTimeFormat("en-US", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date);
  const get = (t) => Number(parts.find((p) => p.type === t).value);
  return Math.floor(Date.UTC(get("year"), get("month") - 1, get("day")) / 86400000);
}

export function groupLabel(isoString, now = new Date(), timeZone = userTimeZone()) {
  const diff = dayIndex(now, timeZone) - dayIndex(new Date(isoString), timeZone);
  if (diff <= 0) return "Today"; // also covers small clock skew (future timestamps)
  if (diff === 1) return "Yesterday";
  if (diff <= 7) return "Previous 7 Days";
  return "Older";
}

export function groupConversations(items, now = new Date(), timeZone = userTimeZone()) {
  const buckets = new Map(GROUP_ORDER.map((l) => [l, []]));
  const sorted = [...items].sort((a, b) => Date.parse(b.last_message_at) - Date.parse(a.last_message_at));
  for (const c of sorted) buckets.get(groupLabel(c.last_message_at, now, timeZone)).push(c);
  return GROUP_ORDER.filter((l) => buckets.get(l).length).map((label) => ({ label, items: buckets.get(label) }));
}

export function formatItemTime(isoString, now = new Date(), timeZone = userTimeZone()) {
  const d = new Date(isoString);
  const label = groupLabel(isoString, now, timeZone);
  if (label === "Today" || label === "Yesterday") return new Intl.DateTimeFormat(undefined, { timeZone, hour: "numeric", minute: "2-digit" }).format(d);
  if (label === "Previous 7 Days") return new Intl.DateTimeFormat(undefined, { timeZone, weekday: "short" }).format(d);
  return new Intl.DateTimeFormat(undefined, { timeZone, day: "numeric", month: "short" }).format(d);
}

export function formatMessageTime(isoString, timeZone = userTimeZone()) {
  return new Intl.DateTimeFormat(undefined, { timeZone, hour: "numeric", minute: "2-digit" }).format(new Date(isoString));
}
