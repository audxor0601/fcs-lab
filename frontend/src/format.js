export const fmt = (v) =>
  v === null || v === undefined ? "—" : v.toFixed(3);

export const ZONE_LABEL = {
  front: "정면",
  rear: "후면",
  side: "측면",
  unknown: "미상",
};
