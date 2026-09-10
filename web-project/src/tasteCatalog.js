import catalogSeed from './catalogSeed.json';

// Item data (id/category/name/imageFilename) lives in catalogSeed.json, the
// same file the backend reads to seed its SQLite catalog
// (web-project/backend/app/catalog.py). This file only adds the per-category
// label/prompt copy shown before the live /api/catalog response arrives.
const CATALOG_DETAILS = {
  artist: {
    label: 'Artist',
    prompt: 'Choose an artist that represents your taste.',
  },
  movie: {
    label: 'Movie',
    prompt: 'Choose a film that evokes your taste.',
  },
  show: {
    label: 'Show',
    prompt: 'Choose a show that describes your taste.',
  },
};

const buildCatalog = () => {
  const catalog = Object.fromEntries(
    Object.entries(CATALOG_DETAILS).map(([category, details]) => [
      category,
      { ...details, options: [] },
    ])
  );

  catalogSeed.forEach((item) => {
    if (!catalog[item.category]) {
      return;
    }

    catalog[item.category].options.push({
      id: item.id,
      name: item.name,
      imageUrl: `${process.env.PUBLIC_URL}/images/${item.imageFilename}`,
    });
  });

  return catalog;
};

const tasteCatalog = buildCatalog();

export const categoryOrder = ['artist', 'movie', 'show'];

export default tasteCatalog;
