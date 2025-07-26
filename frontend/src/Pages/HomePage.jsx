import { motion } from "motion/react";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import CustomButton from "../Components/CustomButton";
import { MyBox } from "../Components/MotionComponents";

function HomePage() {
  return (
    <>
      <MyBox
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0, transition: { duration: 1 } }}
        exit={{ opacity: 0, y: -100, transition: { duration: 1 } }}
        sx={{
          flexGrow: 1,
          backgroundColor: "light-blue",
          paddingLeft: "20vw",
          paddingTop: "20vh",
        }}
      >
        <Grid
          container
          spacing={8}
          sx={{ flexGrow: 1, flexDirection: "column" }}
        >
          <Grid size={8}>
            <motion.div>
              <Typography
                variant="h2"
                gutterBottom
                sx={{
                  color: "whitesmoke",
                  fontWeight: 800,
                }}
              >
                Work Integrated <br></br>
                Learning
              </Typography>
            </motion.div>
            <motion.div>
              <Typography
                variant="subtitle"
                gutterBottom
                sx={{ color: "whitesmoke", marginTop: "2vh", fontWeight: 600 }}
              >
                Insights & Reports RIGHT HERE
              </Typography>
            </motion.div>
          </Grid>
          <Grid size={1}>
            <CustomButton
              title={"Get Started"}
              navigateTo={"/report"}
            ></CustomButton>
          </Grid>
        </Grid>
      </MyBox>
    </>
  );
}

export default HomePage;
