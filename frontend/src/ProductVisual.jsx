import React from "react";

import creamJar from "./assets/figma/cream-jar.png";
import foamCleanser from "./assets/figma/foam-cleanser.png";
import pumpBottle from "./assets/figma/pump-bottle.png";
import serumSpray from "./assets/figma/serum-spray.png";
import spfTube from "./assets/figma/spf-tube.png";
import tonerBottle from "./assets/figma/toner-bottle.png";

const FALLBACK_ART = {
  cleanser: foamCleanser,
  toner: tonerBottle,
  serum: serumSpray,
  treatment: pumpBottle,
  moisturizer: creamJar,
  mask: creamJar,
  spf: spfTube,
  exfoliation: pumpBottle,
  other: pumpBottle,
};

export default function ProductVisual({ product, compact = false }) {
  const imageUrl = product?.image_url;
  const fallback = FALLBACK_ART[product?.routine_step] || FALLBACK_ART.other;
  const [imageState, setImageState] = React.useState(
    imageUrl ? "loading" : "fallback",
  );

  React.useEffect(() => {
    setImageState(imageUrl ? "loading" : "fallback");
    if (!imageUrl) return undefined;

    const timeout = window.setTimeout(() => {
      setImageState((current) =>
        current === "ready" ? current : "failed",
      );
    }, 5000);
    return () => window.clearTimeout(timeout);
  }, [imageUrl]);

  const remoteReady = imageState === "ready";
  const handleLoad = (event) => {
    const { naturalWidth, naturalHeight } = event.currentTarget;
    setImageState(
      naturalWidth >= 80 && naturalHeight >= 80 ? "ready" : "failed",
    );
  };

  return (
    <div
      className={`productArtwork${remoteReady ? " photo" : " illustrated"}${compact ? " compact" : ""}`}
      data-image-state={imageState}
    >
      <img
        className="productFallback"
        src={fallback}
        alt=""
        aria-hidden="true"
      />
      {imageUrl && imageState !== "failed" ? (
        <img
          className={`productPhoto${remoteReady ? " ready" : ""}`}
          src={imageUrl}
          alt={product?.name || "Средство"}
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer"
          onLoad={handleLoad}
          onError={() => setImageState("failed")}
        />
      ) : null}
    </div>
  );
}
