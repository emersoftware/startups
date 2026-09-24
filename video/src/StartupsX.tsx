import type { CSSProperties, ReactNode } from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  interpolateColors,
  useCurrentFrame,
} from "remotion";
import { STAGES } from "./cardda";
import { MORE, ROWS, type Ev } from "./data";
import { C, FONT, L } from "./theme";

// Una sola escena continua. La fila de Cardda nace como la línea bajo el titular,
// se vuelve una serie entre otras, se amplía para contar sus etapas y vuelve al conjunto.
//
//   0–6 s    titular + la línea se dibuja
//   6–12 s   la línea se vuelve una serie entre otras
//   12–22 s  zoom a Cardda y sus etapas
//   22–29 s  vuelve al conjunto y cierre

const inOut = Easing.bezier(0.65, 0, 0.35, 1);
const out = Easing.bezier(0.16, 1, 0.3, 1);
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

const yearOf = (left: number) => 2018 + (left / 100) * 9;
// Geometría
const ROW0 = 540; // lane de la primera fila en la vista de conjunto
const STEP = 84;
const A_LANE = 960; // la línea bajo el titular inicial
const Z_LANE = 520; // lane de Cardda ampliada
const DENSE0 = 430;
const DENSE_STEP = 42;
const NAMED = ROWS.length;
const MORE_ROWS = MORE.slice(0, 15 - NAMED);

// Tiempos (frames a 30 fps)
const T = {
  aOut: [166, 190],
  bIn: 190,
  bOut: [348, 370],
  zoomIn: [362, 410],
  othersOut: [356, 392],
  cText1: 396,
  cText2: 424,
  stages: [415, 490, 545, 610],
  moves: [
    [465, 490],
    [520, 545],
    [578, 610],
  ],
  zoomOut: [672, 712],
  cOut: [658, 672],
  dense: [728, 772],
  close1: 734,
  close2: 782,
  close3: 810,
};

type Border = { w: number; style: string; color: string } | null;
const parseBorder = (b: string): Border => {
  const m = b.match(/([\d.]+)px (\w+) (#\w+)/);
  return m ? { w: Number(m[1]), style: m[2], color: m[3] } : null;
};

const Marker = ({
  ev,
  x,
  y,
  size,
  scale,
  opacity = 1,
  ring = 0,
}: {
  ev: Ev;
  x: number;
  y: number;
  size: number;
  scale: number;
  opacity?: number;
  ring?: number;
}) => {
  const k = size / 10;
  const b = parseBorder(ev.border);
  const tone = b ? b.color : ev.fill;
  const base: CSSProperties = {
    position: "absolute",
    left: x,
    top: y,
    width: size,
    height: size,
    borderRadius: 3 * k,
  };
  return (
    <>
      {ring > 0 && ring < 1 ? (
        <div
          style={{
            ...base,
            border: `${2.5}px solid ${tone}`,
            opacity: (1 - ring) * 0.55 * opacity,
            transform: `translate(-50%,-50%) scale(${1 + ring * 1.4})`,
          }}
        />
      ) : null}
      <div
        style={{
          ...base,
          background: ev.fill,
          border: b ? `${b.w * k}px ${b.style} ${b.color}` : 0,
          boxShadow: `0 0 0 ${3 * k}px #ffffff`,
          opacity,
          transform: `translate(-50%,-50%) scale(${scale})`,
        }}
      />
    </>
  );
};

const Text = ({
  top,
  size,
  children,
  style,
}: {
  top: number;
  size: number;
  children: ReactNode;
  style?: CSSProperties;
}) => (
  <div
    style={{
      position: "absolute",
      left: L,
      right: W_PAD,
      top,
      fontSize: size,
      lineHeight: 1.1,
      letterSpacing: "-0.025em",
      color: C.ink,
      ...style,
    }}
  >
    {children}
  </div>
);
const W_PAD = 60;

// "post": 1080 × 1350 (4:5). "story": 1080 × 1920 (9:16) para Reels/TikTok/historias:
// la composición se centra y el eje se acorta a la derecha para no quedar bajo
// los botones laterales de la app.
const A_SCRIPT = 166; // fin del titular inicial en frames de guion
const A_FRAMES = 92; // cuánto dura en pantalla (~3 s)
export const DURATION = 870 - A_SCRIPT + A_FRAMES;

export type Format = "post" | "story";

export const StartupsX = ({ format = "post" }: { format?: Format }) => {
  const story = format === "story";
  const R = story ? 950 : 1000;
  const OY = story ? 255 : 0;
  // El titular inicial dura ~3 s: la primera escena corre acelerada y el resto
  // sigue a velocidad normal. Todos los tiempos de abajo están en frames "de
  // guion" (f); la duración real es DURATION.
  const g = useCurrentFrame();
  const f = g < A_FRAMES ? g * (A_SCRIPT / A_FRAMES) : g - A_FRAMES + A_SCRIPT;
  const t = (a: number, b: number, e = inOut) =>
    interpolate(f, [a, b], [0, 1], {
      easing: e,
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

  // Dominio temporal del eje: 2018–2027 en conjunto, 2018,5–2025 al ampliar.
  const zoom =
    t(T.zoomIn[0], T.zoomIn[1]) * (1 - t(T.zoomOut[0], T.zoomOut[1]));
  const d0 = lerp(2018, 2018.5, zoom);
  const d1 = lerp(2027, 2025, zoom);
  const xOf = (year: number) => L + ((year - d0) / (d1 - d0)) * (R - L);
  const dense = t(T.dense[0], T.dense[1]);

  const markerSize = lerp(20, 34, zoom) - 3 * dense;
  const pop = (headX: number, x: number) =>
    interpolate(headX - x, [-6, 26], [0, 1], {
      easing: Easing.out(Easing.back(2.2)),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

  // --- Cardda ---
  const denseY = (k: number) => DENSE0 + k * DENSE_STEP;
  const cy =
    A_LANE +
    (ROW0 - A_LANE) * t(176, 214) +
    (Z_LANE - ROW0) * t(T.zoomIn[0], T.zoomIn[1]) +
    (ROW0 - Z_LANE) * t(T.zoomOut[0], T.zoomOut[1]) +
    (denseY(0) - ROW0) * dense;
  const drawA = t(14, 150, Easing.bezier(0.4, 0, 0.3, 1));

  const cardda = ROWS[0];
  const stageEv = STAGES.map((s) =>
    cardda.events.findIndex((e) => e.date === s.date),
  );
  const stageYear = stageEv.map((i) => yearOf(cardda.events[i].left));
  const headYear =
    stageYear[0] +
    T.moves.reduce(
      (acc, [a, b], i) => acc + (stageYear[i + 1] - stageYear[i]) * t(a, b),
      0,
    );
  const traceOp = t(405, 418) * (1 - t(712, 760));

  // --- Filas ---
  type Placed = {
    key: string;
    row: (typeof ROWS)[number];
    y: number;
    draw: number;
    op: number;
    nameOp: number;
    named: boolean;
  };
  const placed: Placed[] = [];
  const hideOthers = 1 - t(T.othersOut[0], T.othersOut[1]) + t(678, 714);
  ROWS.forEach((row, i) => {
    if (i === 0) {
      const namedOp = t(196, 222) * (1 - t(T.dense[0] - 4, T.dense[0] + 20));
      placed.push({
        key: row.name,
        row,
        y: cy,
        draw: drawA,
        op: 1,
        nameOp: namedOp,
        named: true,
      });
      return;
    }
    const s = 198 + i * 12;
    const base = ROW0 + i * STEP;
    const y =
      base +
      360 * t(T.othersOut[0], T.othersOut[1]) -
      360 * t(678, 714) +
      (denseY(i) - base) * dense;
    placed.push({
      key: row.name,
      row,
      y,
      draw: t(s, s + 75, out),
      op: hideOthers,
      nameOp: t(s - 4, s + 16) * (1 - t(T.dense[0] - 4, T.dense[0] + 20)),
      named: true,
    });
  });
  MORE_ROWS.forEach((row, j) => {
    const s = 198 + (NAMED + j) * 12;
    const base = ROW0 + (NAMED + j) * STEP - (STEP - 44) * j;
    const y =
      base +
      360 * t(T.othersOut[0], T.othersOut[1]) -
      360 * t(678, 714) +
      (denseY(NAMED + j) - base) * dense;
    const fadeB = [0.45, 0.2, 0.08][j] ?? 0;
    placed.push({
      key: `more-${j}`,
      row,
      y,
      draw: t(s, s + 58, out),
      op: hideOthers * lerp(fadeB, 1, dense),
      nameOp: 0,
      named: false,
    });
  });

  // Etiqueta de Cardda: "Cardda · Rentz" (como en el sitio) ⇄ "Rentz → Cardda" al ampliar.
  const cLabel = t(406, 416) * (1 - t(662, 672));
  const siteLabel = f < 540 ? 1 - t(396, 405) : t(676, 690);
  const arrow = t(T.stages[1] - 12, T.stages[1] + 6, out);
  const labelSize = lerp(36, 60, zoom);
  const labelTop = cy - lerp(57, 140, zoom);

  // Eje de años
  const axisOverview = t(206, 236) * (1 - t(350, 372)) + t(692, 718);
  const axisZoom = t(398, 424) * (1 - t(660, 676));
  const axisA = t(50, 95) * (1 - t(T.aOut[0], T.aOut[1]));
  const years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];

  const axis = (y: number, op: number, size: number, oddOp: number) =>
    op > 0.001 ? (
      <div style={{ position: "absolute", left: 0, top: 0, opacity: op }}>
        {years.map((yr) => {
          const x = xOf(yr);
          const odd = yr % 2 === 1;
          const o = odd ? oddOp : 1;
          if (x < L - 1 || x > R - 40 || o < 0.01) return null;
          return (
            <div
              key={yr}
              style={{
                position: "absolute",
                left: x,
                top: y,
                fontSize: size,
                color: C.axis,
                opacity: o,
                transform: x <= L + 1 ? "none" : "translateX(-50%)",
              }}
            >
              {yr}
            </div>
          );
        })}
      </div>
    ) : null;

  const lane = (p: Placed) => {
    const headX = lerp(L, R, p.draw);
    const isCardda = p.key === "Cardda";
    return (
      <div
        key={p.key}
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: "100%",
          height: "100%",
          opacity: p.op,
        }}
      >
        {/* marcas de año, como las del carril del sitio */}
        {years.map((yr) => {
          const x = xOf(yr);
          const o = yr % 2 === 1 ? zoom : 1;
          if (p.draw <= 0 || x < L || x > R || x >= headX - 4 || o < 0.01)
            return null;
          const hh = lerp(40, 56, zoom) * (1 - 0.35 * dense);
          return (
            <div
              key={yr}
              style={{
                position: "absolute",
                left: x - 1,
                top: p.y - hh / 2,
                width: 2,
                height: hh,
                background: C.tick,
                opacity: o,
              }}
            />
          );
        })}
        <div
          style={{
            position: "absolute",
            left: L,
            top: p.y - 1,
            width: headX - L,
            height: 2,
            background: C.lane,
          }}
        />
        {isCardda && traceOp > 0.001 ? (
          <div
            style={{
              position: "absolute",
              left: xOf(stageYear[0]),
              top: p.y - 2,
              width: Math.max(0, xOf(headYear) - xOf(stageYear[0])),
              height: 4,
              background: C.ink,
              opacity: traceOp,
            }}
          />
        ) : null}
        {p.row.events.map((ev, i) => {
          const x = xOf(yearOf(ev.left));
          if (x < L - 20 || x > R + 20) return null;
          let scale = pop(headX, x);
          let op = 1;
          let ring = 0;
          if (isCardda) {
            const k = stageEv.indexOf(i);
            if (k >= 0) {
              const a = T.stages[k];
              const bump = interpolate(f, [a - 6, a + 4, a + 26], [0, 1, 0.3], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              scale *= 1 + 0.3 * bump * zoom;
              ring = f >= a && f < a + 26 ? t(a, a + 26, out) : 0;
            } else {
              op = 1 - 0.72 * zoom; // capital: presente pero en segundo plano
            }
          }
          return (
            <Marker
              key={i}
              ev={ev}
              x={x}
              y={p.y}
              size={markerSize}
              scale={scale}
              opacity={op}
              ring={ring}
            />
          );
        })}
        {p.named && !isCardda && p.nameOp > 0.001 ? (
          <div
            style={{
              position: "absolute",
              left: L,
              top: p.y - 57,
              fontSize: 36,
              color: C.ink,
              opacity: p.nameOp,
              letterSpacing: "-0.01em",
            }}
          >
            {p.row.name}
          </div>
        ) : null}
      </div>
    );
  };

  // Titulares
  const aOut = t(T.aOut[0], T.aOut[1]);
  const lineIn = (start: number, i: number) => {
    const k = t(start + i * 5, start + i * 5 + 22, out);
    return { opacity: k, transform: `translateY(${(1 - k) * 26}px)` };
  };
  const bOut = t(T.bOut[0], T.bOut[1]);
  const cOut = t(T.cOut[0], T.cOut[1]);
  const star = interpolate(
    g % 60,
    [0, 8, 15, 23, 30, 38, 60],
    [0, 72, 72, 144, 144, 216, 216],
    {
      easing: inOut,
    },
  );

  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT, color: C.ink }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: OY,
          width: "100%",
          height: 1350,
        }}
      >
        {/* 0–6 s */}
        <div
          style={{
            opacity: 1 - aOut,
            transform: `translateY(${-30 * aOut}px)`,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: L,
              top: 96,
              display: "flex",
              alignItems: "center",
              gap: 20,
            }}
          >
            <span
              style={{
                width: 50,
                height: 50,
                background: C.accent,
                borderRadius: 14,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg width="30" height="30" viewBox="0 0 24 24">
                <g transform={`translate(12 12) rotate(${star})`}>
                  <path
                    fill="#ffffff"
                    transform="translate(-12.0003 -12.5779)"
                    d="M12 2l2.94 6.34L22 9.27l-5 4.73 1.18 6.99L12 17.77 5.82 21l1.18-6.99-5-4.73 7.06-.93z"
                  />
                </g>
              </svg>
            </span>
            <span style={{ fontSize: 36, letterSpacing: "-0.01em" }}>
              Chile, Startups
            </span>
          </div>
          <Text top={420} size={88}>
            Quería saber
            <br />
            cómo pivotean
            <br />
            las startups
            <br />
            en Chile.
          </Text>
        </div>

        {/* 6–12 s */}
        {f >= T.bIn - 2 && f < T.bOut[1] + 2 ? (
          <Text
            top={110}
            size={72}
            style={{
              opacity: 1 - bOut,
              transform: `translateY(${-30 * bOut}px)`,
            }}
          >
            <div style={lineIn(T.bIn, 0)}>Terminé reconstruyendo</div>
            <div style={lineIn(T.bIn, 1)}>
              más de <span style={{ color: C.accent }}>80 trayectorias</span>
            </div>
            <div style={lineIn(T.bIn, 2)}>de startups de Platanus.</div>
          </Text>
        ) : null}

        {/* 12–22 s */}
        {f >= T.cText1 - 2 && f < T.cOut[1] + 2 ? (
          <Text top={110} size={76} style={{ opacity: 1 - cOut }}>
            <div style={lineIn(T.cText1, 0)}>Qué ofrecían.</div>
            <div style={lineIn(T.cText2, 0)}>Qué fue cambiando.</div>
          </Text>
        ) : null}

        {/* Series */}
        {axis(cy + 34, axisA, 28, 0)}
        {axis(
          lerp(440, denseY(0) - 58, dense),
          Math.min(1, axisOverview),
          28,
          0,
        )}
        {axis(Z_LANE + 44, axisZoom, 30, 1)}
        {[...placed].reverse().map(lane)}

        {/* Etiqueta de Cardda */}
        <div
          style={{
            position: "absolute",
            left: L,
            top: labelTop,
            fontSize: labelSize,
            letterSpacing: "-0.02em",
            whiteSpace: "nowrap",
          }}
        >
          <span
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              opacity: placed[0].nameOp * siteLabel,
            }}
          >
            Cardda
            <span style={{ color: C.alias, fontSize: "0.8em" }}> · Rentz</span>
          </span>
          <span
            style={{ position: "absolute", left: 0, top: 0, opacity: cLabel }}
          >
            Rentz
            <span
              style={{
                display: "inline-block",
                opacity: arrow,
                transform: `translateX(${(1 - arrow) * -24}px)`,
              }}
            >
              &nbsp;→ Cardda
            </span>
          </span>
        </div>

        {/* Etapas */}
        {f >= T.stages[0] - 8 && f < T.cOut[1] + 2
          ? STAGES.map((s, k) => {
              const a = T.stages[k];
              const inK = t(a - 6, a + 14, out);
              const next = T.stages[k + 1];
              const dim = next ? t(next - 4, next + 12) : 0;
              return (
                <div
                  key={s.date}
                  style={{
                    position: "absolute",
                    left: L,
                    right: W_PAD,
                    top: 680 + k * 148,
                    opacity: inK * (1 - cOut),
                    transform: `translateY(${(1 - inK) * 24}px)`,
                  }}
                >
                  <div style={{ fontSize: 34, color: C.muted }}>
                    {s.caption}
                  </div>
                  <div
                    style={{
                      fontSize: 52,
                      letterSpacing: "-0.02em",
                      marginTop: 8,
                      color: interpolateColors(dim, [0, 1], [C.ink, "#8a867e"]),
                    }}
                  >
                    {s.text}
                  </div>
                </div>
              );
            })
          : null}

        {/* Cierre */}
        {f >= T.close1 - 2 ? (
          <>
            <Text top={110} size={76}>
              <div style={lineIn(T.close1, 0)}>Cada historia,</div>
              <div style={lineIn(T.close1, 1)}>con sus fuentes.</div>
            </Text>
            <Text
              top={1090}
              size={58}
              style={{ color: C.accent, ...lineIn(T.close2, 0) }}
            >
              startups.emersoftware.cl
            </Text>
            <Text top={1186} size={46} style={lineIn(T.close3, 0)}>
              Va el hilo ↓
            </Text>
          </>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
