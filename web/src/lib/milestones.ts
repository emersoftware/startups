/** One milestone per month; retain every source event inside it. */
export function mergeMilestones<T extends { date: string; type: string }>(events: T[]) {
  const months = new Map<string, T[]>();
  for (const event of events) {
    const month = event.date.slice(0, 7);
    const members = months.get(month) ?? [];
    members.push(event);
    months.set(month, members);
  }
  return [...months.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([date, members]) => ({
    date,
    type: members[0].type,
    members,
  }));
}
