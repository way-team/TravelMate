export class UserProfile {
  user: User;
  age: Number;
  email: string;
  first_name: string;
  last_name: string;
  description: string;
  birthdate: string;
  city: string;
  nationality: string;
  photo: string;
  discoverPhoto: string;
  avarageRate: Number;
  numRate: Number;
  isPremium: boolean;
  datePremium: Date;
  status: string;
  profesion: string;
  civilStatus: string;
  gender: string;
  languages: string[];
  interests: string[];
  created_trips: Trip[];
  past_joined_trips: Trip[];
  future_joined_trips: Trip[];
  active_joined_trips: Trip[];
}
export class Language {
  name: String;
}
export class Interest {
  name: String;
}

export class Trip {
  id: Number;
  title: String;
  price: Number;
  description: String;
  startDate: Date;
  endDate: Date;
  tripType: String;
  image: String;
  userImage: String;
  status: Boolean;
  user_id: Number;
  creator: string;
  cities: string[];
}

export class City {
  country: {
    name: String;
  };
  trips: [
    {
      creator: String;
      title: String;
      description: String;
      startDate: String;
      endDate: String;
      image: String;
      status: boolean;
    }
  ];
  name: String;
  id: Number;
}

export class User {
  id: Number;
  username: string;
}

export class test {
  count: string;
  next: string;
  previous: string;
  results: User[];
}

export class application_user {
  applicantName: string;
  applicationId: string;

  constructor(applicantName: string, applicationId: string) {
    this.applicantName = applicantName;
    this.applicationId = applicationId;
  }
}
