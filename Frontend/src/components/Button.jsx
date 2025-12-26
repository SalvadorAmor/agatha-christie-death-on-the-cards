import React from "react";

//botón genérico
function Button({label, onClick, disabled, className}) {
  //label es nombre, onclick lo q hace al clickear, enable si está habilitadp y classname es como lo vamos a usar en otras cosas
  return (
    <button //aca podria ir btn lg creo
      className={className}
      disabled = {disabled}
      onClick={onClick} //funcion
    >
    {label}
</button>
  );
}
export const whiteButtonStyle = "rounded-xl bg-white text-black font-semibold px-6 py-2.5 cursor-pointer transition-all duration-200 ease-in-out hover:shadow-[0_0_20px_#ff4d4d] hover:scale-105";
export const redButtonStyle = "rounded-xl bg-red-900 text-white font-semibold px-6 py-2.5 cursor-pointer transition-all duration-200 ease-in-out hover:shadow-[0_0_20px_#ff4d4d] hover:scale-105";
export const darkButtonStyle = "rounded-xl bg-[#230812] text-white font-semibold px-6 py-2.5 cursor-pointer transition-all duration-200 ease-in-out hover:shadow-[0_0_20px_#ff4d4d] hover:scale-105";
export const buttonTransition = "transition-all duration-200 ease-in-out hover:shadow-[0_0_20px_#ff4d4d] hover:scale-105";
export default Button;
//disabled es un atributo de html, por eso debe ser si o si disabled y no se puede hacer con enabled
