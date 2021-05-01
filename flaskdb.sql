-- phpMyAdmin SQL Dump
-- version 4.9.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le :  Dim 02 mai 2021 à 00:30
-- Version du serveur :  10.4.8-MariaDB
-- Version de PHP :  7.3.11

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données :  `flaskdb`
--

-- --------------------------------------------------------

--
-- Structure de la table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `users`
--

INSERT INTO `users` (`id`, `name`, `username`, `password`) VALUES
(1, 'test', 'tester', 'test123'),
(2, 'bob', 'marley', '$5$rounds=535000$vAcHuOD.X9Il.VKp$dcIDPldBHNDtK.n/'),
(3, 'messi', 'messi', '$5$rounds=535000$ejih8EG1xIFhqq1W$cWzph6JFpQfJvXd9'),
(4, 'benzema', 'benzema', '$5$rounds=535000$pXwqAg1ZnRv3x4na$zUItGhhhCPHQbQBfCe18uLxNqV/os05KPY0haddlMg1'),
(5, 'lastTest', 'lastTest', '$5$rounds=535000$hKhSsWWc3IPovIKs$9NM3kpYn3q9jK0R8.sXUIkqp0k.m/BiLgH7A8kcJSz4'),
(6, 'love', 'love', '$5$rounds=535000$/IBp4e.3WzyUuMdY$ofF2ePOZOygz/YTvlwPr.6sWEfdlSpoxltS.k0GgXlC'),
(7, 'mane', 'mane', '$5$rounds=535000$7rcifkdGDlcEVHVZ$0R3ddy8IOcC6aOcD.SkScsFXkbC.D6Zqrsb7FL2ImAA');

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
