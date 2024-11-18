import React from "react";

// 型定義をインポートまたは上記で定義
interface Todo {
  id: number;
  title: string;
  completed: boolean;
  attachment?: string;
}

interface TodoItemProps {
  todo: Todo;
  toggleTodoCompletion: (id: number, completed: boolean) => void;
}

const TodoItem: React.FC<TodoItemProps> = ({ todo, toggleTodoCompletion }) => {
  return (
    <li>
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => toggleTodoCompletion(todo.id, !todo.completed)}
      />
      <span style={{ display: "inline-flex", gap: "10px" }}>
        <strong>{todo.title}</strong>
        {todo.attachment && (
          <a href={todo.attachment} target="_blank" rel="noopener noreferrer">
            View Attachment
          </a>
        )}
      </span>
    </li>
  );
};

export default TodoItem;
