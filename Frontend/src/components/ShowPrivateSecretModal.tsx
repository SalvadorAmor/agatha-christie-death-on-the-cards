import { redButtonStyle } from "./Button";

export type Secret = {
  id: number;
  owner: number;
  name: string;
  revealed: boolean;
  type: string;
};

type ShowPrivateSecretModalProps = {
  open: boolean;
  secret: number | null;
  secrets: Secret[];
  onClose: () => void;
};

export default function ShowPrivateSecretModal({ open, secret, onClose, secrets }: ShowPrivateSecretModalProps) {
  if (!open || !secret) return null;

  const getSecretImage = (type: string) => {
    if (type === "murderer") return "/images/secrets/youre-the-murderer.png";
    if (type === "accomplice") return "/images/secrets/youre-the-accomplice.png";
    return "/images/secrets/varios.png"; 
  };

  const secret_to_reveal = secrets.find((s) => s.id === secret);
  if(!secret_to_reveal) return;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-opacity-60 fade">
      <div className="bg-[#230812] p-8 rounded-3xl shadow-lg w-80 max-w-full text-white fade-pop">
        <h2 className="text-2xl font-bold mb-4 text-center">¡Shh! Descubriste un secreto</h2>
        <div className="text-center mb-6">
          <img
            src={getSecretImage(secret_to_reveal.type)}
            alt={`Secreto: ${secret_to_reveal.name}`}
            className="w-24 h-32 mx-auto mb-4 rounded-lg object-cover"
          />
        </div>
        <div className="flex justify-center">
          <button
            onClick={onClose}
            className={redButtonStyle}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
