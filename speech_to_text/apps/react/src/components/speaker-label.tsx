import { getSpeakerColor } from "../utils/speaker-colors";

interface SpeakerLabelProps {
  speakerNumber: string | number;
  className?: string;
}

export default function SpeakerLabel({ speakerNumber }: SpeakerLabelProps) {
  const speakerColor = getSpeakerColor(speakerNumber);

  return (
    <div
      className="font-bold uppercase text-sm mt-2 block"
      style={{ color: speakerColor }}
    >
      Speaker {speakerNumber}:
    </div>
  );
}
