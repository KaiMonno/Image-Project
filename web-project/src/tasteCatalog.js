const tasteCatalog = {
  artist: {
    label: 'Artist',
    prompt: 'Choose an artist that represents your taste.',
    options: [
      {
        id: 'local-artist',
        name: 'Local Artist',
        description: 'Current local artist image.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image1.jpeg`,
      },
    ],
  },
  movie: {
    label: 'Movie',
    prompt: 'Choose a film that evokes your taste.',
    options: [
      {
        id: 'local-movie',
        name: 'Local Movie',
        description: 'Current local movie poster.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image2.jpg`,
      },
    ],
  },
  show: {
    label: 'Show',
    prompt: 'Choose a show that describes your taste.',
    options: [
      {
        id: 'local-show',
        name: 'Local Show',
        description: 'Current local show image.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image3.jpg`,
      },
    ],
  },
};

export const categoryOrder = ['artist', 'movie', 'show'];

export default tasteCatalog;
