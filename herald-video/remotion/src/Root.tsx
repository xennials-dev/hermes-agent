import React from "react";
import { Composition } from "remotion";
import { HeraldVideo } from "./HeraldVideo";

export const Root: React.FC = () => {
  return (
    <Composition
      id="HeraldVideo"
      component={HeraldVideo}
      durationInFrames={2700} // 90 seconds at 30 fps (3 x 30s segments = 900 frames each)
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
