const tasteCatalog = {
  artist: {
    label: 'Artist',
    prompt: 'Choose an artist that represents your taste.',
    options: [
      {
        id: 'artist-weeknd',
        name: 'The Weeknd',
        imageUrl: `${process.env.PUBLIC_URL}/images/artist-weeknd.jpg`,
      },
      {
        id: 'artist-olivia-rodrigo',
        name: 'Olivia Rodrigo',
        imageUrl: `${process.env.PUBLIC_URL}/images/artist-olivia-rodrigo.jpg`,
      },
      {
        id: 'artist-drake',
        name: 'Drake',
        imageUrl: `${process.env.PUBLIC_URL}/images/artist-drake.jpg`,
      },
    ],
  },
  movie: {
    label: 'Movie',
    prompt: 'Choose a film that evokes your taste.',
    options: [
      {
        id: 'movie-2001-space-odyssey',
        name: '2001: A Space Odyssey',
        imageUrl: `${process.env.PUBLIC_URL}/images/movie-2001-space-odyssey.jpg`,
      },
      {
        id: 'movie-shawshank-redemption',
        name: 'The Shawshank Redemption',
        imageUrl: `${process.env.PUBLIC_URL}/images/movie-shawshank-redemption.jpg`,
      },
      {
        id: 'movie-godfather',
        name: 'The Godfather',
        imageUrl: `${process.env.PUBLIC_URL}/images/movie-godfather.jpg`,
      },
    ],
  },
  show: {
    label: 'Show',
    prompt: 'Choose a show that describes your taste.',
    options: [
      {
        id: 'show-planet-earth',
        name: 'Planet Earth',
        imageUrl: `${process.env.PUBLIC_URL}/images/show-planet-earth.jpg`,
      },
      {
        id: 'show-avatar-last-airbender',
        name: 'Avatar: The Last Airbender',
        imageUrl: `${process.env.PUBLIC_URL}/images/show-avatar-last-airbender.jpg`,
      },
      {
        id: 'show-the-wire',
        name: 'The Wire',
        imageUrl: `${process.env.PUBLIC_URL}/images/show-the-wire.jpg`,
      },
    ],
  },
};

export const categoryOrder = ['artist', 'movie', 'show'];

export default tasteCatalog;
