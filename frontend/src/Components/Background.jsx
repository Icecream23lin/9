import { MyBox } from "./MotionComponents";

function Background() {
  return (
    <>
      <MyBox
        sx={{
          position: "fixed",
          width: "100vw",
          height: "100vh",
          top: 0,
          left: 0,
          backgroundImage: "url('/bg.jpg')",
          backgroundPosition: "center",
          backgroundSize: "cover",
          zIndex: "-1",
        }}
      />
      <MyBox
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          zIndex: -1,
        }}
      />
    </>
  );
}
export default Background;
