import axios from "axios";

export const getProgress = async () => {
  const response = await axios.get(
    "http://localhost:8000/progress"
  );

  return response.data;
};