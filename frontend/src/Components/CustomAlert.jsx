import Alert from "@mui/material/Alert";
import Collapse from "@mui/material/Collapse";
import { MyBox } from "./MotionComponents";
import Snackbar from "@mui/material/Snackbar";
function CustomAlert({ children, flag, number, onClose, ...props }) {
  return (
    <Snackbar
      open={flag}
      onClose={onClose}
      anchorOrigin={{ vertical: "top", horizontal: "right" }}
      autoHideDuration={2000}
      style={{ top: number * 80 }}
    >
      <Collapse in={flag}>
        <MyBox sx={{ margin: "0.5rem" }}>
          <Alert {...props}>{children}</Alert>
        </MyBox>
      </Collapse>
    </Snackbar>
  );
}

export default CustomAlert;
