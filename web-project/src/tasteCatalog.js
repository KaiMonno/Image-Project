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
      {
        id: 'fallback-artist-dream-pop',
        name: 'Dream Pop',
        description: 'Soft color, grain, and late-night synth mood.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-artist-dream-pop.jpg`,
      },
      {
        id: 'fallback-artist-jazz-club',
        name: 'Jazz Club',
        description: 'Warm stage lights with a classic live-session feel.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-artist-jazz-club.jpg`,
      },
      {
        id: 'fallback-artist-indie-rock',
        name: 'Indie Rock',
        description: 'High-contrast guitar texture and poster-wall energy.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-artist-indie-rock.jpg`,
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
      {
        id: 'fallback-movie-noir',
        name: 'Neon Noir',
        description: 'Cinematic shadows, rain, and saturated city light.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-movie-noir.jpg`,
      },
      {
        id: 'fallback-movie-sunlit',
        name: 'Sunlit Drama',
        description: 'Open skies, warm light, and quiet character-study tone.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-movie-sunlit.jpg`,
      },
      {
        id: 'fallback-movie-sci-fi',
        name: 'Analog Sci-Fi',
        description: 'Clean geometry with a retro-futurist visual palette.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-movie-sci-fi.jpg`,
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
      {
        id: 'fallback-show-prestige',
        name: 'Prestige Mystery',
        description: 'Moody ensemble staging with a slow-burn atmosphere.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-show-prestige.jpg`,
      },
      {
        id: 'fallback-show-comedy',
        name: 'Bright Comedy',
        description: 'Playful shapes, crisp color, and upbeat sitcom pacing.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-show-comedy.jpg`,
      },
      {
        id: 'fallback-show-adventure',
        name: 'Adventure Serial',
        description: 'Bold landscape forms with serialized cliffhanger energy.',
        imageUrl: `${process.env.PUBLIC_URL}/images/fallback-show-adventure.jpg`,
      },
    ],
  },
};

export const categoryOrder = ['artist', 'movie', 'show'];

export default tasteCatalog;
