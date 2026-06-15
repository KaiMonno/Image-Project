const tasteCatalog = {
  artist: {
    label: 'Artist',
    prompt: 'Pick an artist that represents your sound.',
    options: [
      {
        id: 'artist-visual',
        name: 'Neon Headliner',
        description: 'Bright, high-energy, and stage-ready.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image1.jpeg`,
      },
      {
        id: 'artist-indie',
        name: 'Indie Favorite',
        description: 'Warm, personal, and a little unexpected.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image2.jpg`,
      },
      {
        id: 'artist-classic',
        name: 'Classic Icon',
        description: 'Timeless taste with a polished edge.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image3.jpg`,
      },
    ],
  },
  movie: {
    label: 'Movie',
    prompt: 'Pick a movie that fits your visual taste.',
    options: [
      {
        id: 'movie-dreamy',
        name: 'Dream Sequence',
        description: 'Soft, cinematic, and atmospheric.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image1.jpeg`,
      },
      {
        id: 'movie-action',
        name: 'Midnight Feature',
        description: 'Bold pacing with a dramatic finish.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image2.jpg`,
      },
      {
        id: 'movie-comfort',
        name: 'Comfort Rewatch',
        description: 'Familiar, expressive, and easy to love.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image3.jpg`,
      },
    ],
  },
  show: {
    label: 'Show',
    prompt: 'Pick a show that belongs on your profile.',
    options: [
      {
        id: 'show-binge',
        name: 'Weekend Binge',
        description: 'A little addictive and full of momentum.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image1.jpeg`,
      },
      {
        id: 'show-prestige',
        name: 'Prestige Pick',
        description: 'Carefully made and conversation-worthy.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image2.jpg`,
      },
      {
        id: 'show-comedy',
        name: 'Easy Favorite',
        description: 'Reliable, bright, and rewatchable.',
        imageUrl: `${process.env.PUBLIC_URL}/images/image3.jpg`,
      },
    ],
  },
};

export const categoryOrder = ['artist', 'movie', 'show'];

export default tasteCatalog;
