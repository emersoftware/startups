import { cancelRender, continueRender, delayRender, staticFile } from "remotion";

// Solo existe el peso Regular: no usar fontWeight > 400.
const handle = delayRender("Rubik");
const face = new FontFace("Rubik", `url(${staticFile("Rubik-Regular.ttf")}) format("truetype")`);
face
  .load()
  .then((f) => {
    document.fonts.add(f);
    continueRender(handle);
  })
  .catch((err) => cancelRender(err));
