type Secret = {
    name: string;
    revealed: boolean;
    type: string;
}

type Prop = {
    secret: Secret;
    mine?: boolean;
    chooseSecret: boolean;
    chooseRevealed: boolean;
    isSelected: boolean;
}


export const Secret = ({secret, mine = false, chooseSecret = false, chooseRevealed = false, isSelected = false}: Prop) => {
    const mineRevealed = secret.revealed ? "opacity-100" : (mine ? "brightness-50" : "")
    const hasToPick = (chooseSecret && !secret.revealed) || (chooseRevealed && secret.revealed) ? "hover:border-1 hover:shadow-lg cursor-pointer" : ""
    const size = isSelected ? (mine ? "md:w-22 lg:w-32" : "md:w-12 lg:w-22" ) : (mine ? "md:w-20 lg:w-30" : "md:w-10 lg:w-20")
    return (
        (secret.revealed || mine) ?
        <div className={`${size} ${hasToPick} rounded-xl shadow-red-400 relative`}>
            <img className={`rounded-xl ${mineRevealed}`} src={`/images/secrets/${secret.name}.png`} alt={secret.name}/>
            {(mine && !secret.revealed) &&
            <span 
                className="absolute top-1/2 left-1/2 text-red-800 -translate-1/2 material-symbols-outlined" 
                style={{fontSize: '150'}}>
                visibility_off
            </span>}
        </div>
        :
        <div className={`${size} ${hasToPick} rounded-xl shadow-red-400`}>
            <img className="rounded-xl" src={`/images/secrets/secret-hidden.png`} alt='secret'/>
        </div>
    )
}