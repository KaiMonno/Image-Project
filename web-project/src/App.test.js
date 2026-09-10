import { fireEvent, render, screen } from '@testing-library/react';
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
  expect(
    screen.getByText(/create an image that is representative of your taste and aesthetic/i)
  ).toBeInTheDocument();
  expect(await screen.findByRole('button', { name: /the weeknd/i })).toBeInTheDocument();
  expect(screen.getByRole('searchbox', { name: /search artist/i })).toBeInTheDocument();
});

test('renders without crashing when a fetched catalog category has no options', async () => {
  // The catalog can legitimately have zero options for a category (e.g.
  // after removing every entry via app/manage_catalog.py without adding
  // replacements). The hero preview must not assume options[0] exists.
  const catalogWithNoMovies = {
    ...tasteCatalog,
    movie: { ...tasteCatalog.movie, options: [] },
  };

  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => catalogWithNoMovies,
  });

  render(<App />);

  expect(await screen.findByRole('button', { name: /the weeknd/i })).toBeInTheDocument();
});

test('shows a message instead of a dead end when the next category has no options', async () => {
  const catalogWithNoMovies = {
    ...tasteCatalog,
    movie: { ...tasteCatalog.movie, options: [] },
  };

  global.fetch = jest.fn((input) => {
    const url = typeof input === 'string' ? input : input.url;

    if (url.includes('/api/catalog')) {
      return Promise.resolve({ ok: true, json: async () => catalogWithNoMovies });
    }
    if (url.includes('/upload-image/')) {
      return Promise.resolve({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ status: 'pending', savedCategory: 'artist', remainingCategories: ['movie', 'show'] }),
      });
    }
    // The fetch of the selected option's own imageUrl, turned into a blob.
    return Promise.resolve({ ok: true, blob: async () => new Blob() });
  });

  render(<App />);

  fireEvent.click(await screen.findByRole('button', { name: /the weeknd/i }));
  fireEvent.click(screen.getByRole('button', { name: /confirm artist/i }));

  expect(
    await screen.findByText(/no movie options are in the catalog yet/i)
  ).toBeInTheDocument();
});
