import React, { useState, useEffect } from "react";
import axios from "axios";
import TodoForm from "./TodoForm";
import TodoItem from "./TodoItem";

// Todo型を定義
interface Todo {
  id: number;
  title: string;
  completed: boolean;
}

function App() {
  // useStateの型を指定
  const [todos, setTodos] = useState<Todo[]>([]);

  useEffect(() => {
    async function fetchTodos() {
      try {
        const response = await axios.get<Todo[]>(
          "http://127.0.0.1:8000/api/todos/"
        );
        setTodos(response.data);
      } catch (error) {
        console.error("Error fetching todos:", error);
      }
    }
    fetchTodos();
  }, []);

  // 新しいTodoを追加する関数
  const addTodo = (newTodo: Todo) => {
    setTodos([...todos, newTodo]);
  };

  // Todoの完了状態を切り替える関数
  const toggleTodoCompletion = async (id: number, completed: boolean) => {
    try {
      await axios.patch(`http://127.0.0.1:8000/api/todos/${id}/`, {
        completed,
      });
      setTodos(
        todos.map((todo) => (todo.id === id ? { ...todo, completed } : todo))
      );
    } catch (error) {
      console.error("Error updating todo:", error);
    }
  };

  // 未完了のTodoをフィルタリング
  const incompleteTodos = todos.filter((todo) => !todo.completed);

  // 完了済みのTodoをフィルタリング
  const completedTodos = todos.filter((todo) => todo.completed);

  return (
    <div className="App">
      <h1>Todo List</h1>
      <TodoForm addTodo={addTodo} />

      <h2>Existing Todos</h2>
      <ul>
        {incompleteTodos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            toggleTodoCompletion={toggleTodoCompletion}
          />
        ))}
      </ul>

      <h2>Completed Todos</h2>
      <ul>
        {completedTodos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            toggleTodoCompletion={toggleTodoCompletion}
          />
        ))}
      </ul>
    </div>
  );
}

export default App;
