import { MyBox } from "../Components/MotionComponents";
import { Outlet } from "react-router-dom";
function ReportPage() {
  return (
    <>
      <MyBox
        sx={{
          width: "100vw",
          height: "100vh",
          position: "fixed",
          overflow: "auto",
        }}
      >
        <Outlet></Outlet>
      </MyBox>
    </>
  );
}

export default ReportPage;
