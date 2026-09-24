import "./index.css";
import "./font";
import { Composition } from "remotion";
import { DURATION, StartupsX } from "./StartupsX";

export const RemotionRoot = () => (
  <>
    {/* 9:16 para Reels, TikTok e historias */}
    <Composition
      id="StartupsXStory"
      component={StartupsX}
      defaultProps={{ format: "story" as const }}
      durationInFrames={DURATION}
      fps={30}
      width={1080}
      height={1920}
    />
    {/* 4:5 para el feed de X */}
    <Composition
      id="StartupsX"
      component={StartupsX}
      defaultProps={{ format: "post" as const }}
      durationInFrames={DURATION}
      fps={30}
      width={1080}
      height={1350}
    />
  </>
);
