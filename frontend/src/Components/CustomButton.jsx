import { useNavigate } from "react-router-dom";
import { MyButton } from "./MotionComponents";

function CustomButton({ title, navigateTo, state = null, ...props }) {
  const navigate = useNavigate();
  return (
    <>
      <MyButton
        whileTap={{ scale: 0.95 }}
        {...props}
        sx={{
          whiteSpace: "nowrap",
          backgroundColor: "#1D4ED8",
          fontWeight: "600",
          color: "white",
          borderRadius: "9999px",
          fontSize: "1rem",
          border: "1px solid",
          borderColor: "#1D4ED8",
          paddingY: 2,
          paddingX: 8,
          // Hover styles:
          "&:hover": {
            borderColor: "#3B82F6",
            color: "common.white",
            backgroundColor: "#3B82F6",
          },
        }}
        onClick={() => {
          navigate(navigateTo, { state });
        }}
      >
        {title}
      </MyButton>
    </>
  );
}

export default CustomButton;
