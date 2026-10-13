import React from "react";
import koyashLogo from "./assets/figma/koyash-logo.png";

export default function BrandLogo({ onClick, className = "" }) {
  return (
    <button
      type="button"
      className={`logo ${className}`.trim()}
      onClick={onClick}
      aria-label="Koyash — на главную"
      data-testid="brand-logo"
    >
      <img src={koyashLogo} alt="" width="299" height="103" />
    </button>
  );
}
