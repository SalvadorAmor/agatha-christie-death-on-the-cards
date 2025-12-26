type Prop = {
  source: string;
  className?: string;
  style?: React.CSSProperties;
};

export const Card = ({ source }: Prop) => {
  return (
    <div className="md:w-20 lg:w-35 hover:w-50 hover:border-1 rounded-xl hover:shadow-lg shadow-red-400 cursor-pointer">
      <img
        className="rounded-xl"
        src={`/images/cards/${source}.png`}
        alt={source}
      />
    </div>
  );
};

export const TableCard = ({ source }: Prop) => {
  return (
    <div className="md:w-18 lg:w-33 hover:border-1 rounded-xl hover:shadow-lg shadow-red-400 cursor-pointer">
      <img
        className="rounded-xl"
        src={`/images/cards/${source}.png`}
        alt={source}
      />
    </div>
  );
};

export const DiscardedCard = ({ source,  className  }: Prop) => {
  return (
    <img
     className={`rounded-xl ${className} md:w-15 lg:w-30`}
     src={`/images/cards/${source}.png`}
      alt="carta_descartada"
    />
  );
};
