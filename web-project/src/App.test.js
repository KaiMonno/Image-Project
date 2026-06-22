import { render, screen } from '@testing-library/react';
import App from './App';
import tasteCatalog from './tasteCatalog';

beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => tasteCatalog,
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders the taste builder', async () => {
  render(<App />);
  expect(screen.getByText(/build a snapshot of your taste/i)).toBeInTheDocument();
  expect(await screen.findByRole('button', { name: /local artist/i })).toBeInTheDocument();
  expect(screen.getByRole('searchbox', { name: /search artist/i })).toBeInTheDocument();
});
