/** 백엔드 호출을 한곳에 모은다. 주소가 바뀌면 여기만 고친다. */

async function get(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

export const fetchRuns = () => get("/api/stats/runs");
export const fetchRunDetail = (id) => get(`/api/stats/experiments/${id}`);
export const fetchShots = (id) => get(`/api/experiments/${id}/shots`);

/** 분포도에 뿌릴 개별 탄착만 뽑는다. 지형 오폭은 뺀다. */
export async function fetchMissValues(id) {
  const shots = await fetchShots(id);
  return shots
    .filter((s) => s.kind !== "terrain" && s.miss !== null)
    .map((s) => s.miss);
}
