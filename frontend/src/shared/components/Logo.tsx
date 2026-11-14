import { useId } from "react";

/** Isotipo de ORBIT Health (silueta sin fondo: esquinas HUD, órbita y trazo cardíaco). */
export default function Logo() {
  const clipId = useId();
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="24 12 832 806"
      width="24"
      height="24"
      role="img"
      aria-label="ORBIT Health"
      style={{ flexShrink: 0 }}
    >
      <g fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path
          d="M58 128V42H140M745 42H830V128M830 702V788H745M140 788H58V702"
          stroke="currentColor"
          strokeWidth="22"
        />
        <path d="M690 237A338 338 0 1 0 735 478" stroke="#5f84e8" strokeWidth="24" />
        <defs>
          <clipPath id={clipId}>
            <circle cx="403" cy="413" r="338" />
          </clipPath>
        </defs>
        <circle
          cx="501"
          cy="403"
          r="281"
          clipPath={`url(#${clipId})`}
          stroke="#5f84e8"
          strokeWidth="19"
        />
        <path
          d="M262 410H345L362 372L403 462L438 232L485 575L528 342L555 408H728"
          stroke="currentColor"
          strokeWidth="26"
        />
        <circle cx="785" cy="413" r="38" fill="#25e6ef" stroke="none" />
        <circle cx="115" cy="99" r="14" fill="#5f84e8" stroke="none" />
        <circle cx="770" cy="99" r="14" fill="#5f84e8" stroke="none" />
        <circle cx="113" cy="730" r="14" fill="#5f84e8" stroke="none" />
        <circle cx="770" cy="730" r="14" fill="#5f84e8" stroke="none" />
      </g>
    </svg>
  );
}
