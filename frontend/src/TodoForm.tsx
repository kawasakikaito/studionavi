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
    formData.append("completed", "false");
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
      setTitle("");
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
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New Todo"
          required
          className="px-4 py-2 border rounded-md w-full"
        />
      </div>
      <div>
        <input
          type="file"
          onChange={handleFileChange}
          className="px-4 py-2 border rounded-md w-full"
        />
      </div>
      <button
        type="submit"
        className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
      >
        Add Todo
      </button>
    </form>
  );
};

export default TodoForm;
