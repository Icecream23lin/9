import { MyBox } from "./MotionComponents";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";

function Loading({ message }) {
  return (
    <MyBox
      sx={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-around",
        textAlign: "center",
      }}
    >
      <MyBox>
        <CircularProgress size={"4rem"} />
        <Typography
          variant="body1"
          gutterBottom
          sx={{ padding: "3rem", color: "#1D4ED8" }}
        >
          {message}
        </Typography>
      </MyBox>
    </MyBox>
  );
}

export default Loading;
