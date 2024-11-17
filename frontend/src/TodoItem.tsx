import React, { useState, ChangeEvent, FormEvent } from "react";
import axios from "axios";

// Propsの型定義
interface Todo {
  id: number;
  title: string;
  completed: boolean;
  attachment?: string;
}

interface TodoFormProps {
  addTodo: (newTodo: Todo) => void;
}

const TodoForm: React.FC<TodoFormProps> = ({ addTodo }) => {
  // useStateの型を明示
  const [title, setTitle] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("title", title);
    formData.append("completed", "false"); // フォームデータは文字列として渡す
    if (file) formData.append("attachment", file);

    try {
      const response = await axios.post<Todo>(
        "http://127.0.0.1:8000/api/todos/",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      addTodo(response.data);
      setTitle(""); // フォームをリセット
      setFile(null);
    } catch (error) {
      console.error("Error creating todo:", error);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="New Todo"
        required
      />
      <input type="file" onChange={handleFileChange} />
      <button type="submit">Add Todo</button>
    </form>
  );
};

export default TodoForm;
