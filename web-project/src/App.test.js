import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the taste builder', () => {
  render(<App />);
  expect(screen.getByText(/build a snapshot of your taste/i)).toBeInTheDocument();
  expect(screen.getByText(/loading options from the image database/i)).toBeInTheDocument();
});
