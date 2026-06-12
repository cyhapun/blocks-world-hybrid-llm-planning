(define (problem bw_medium_006)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on d a)
    (clear d)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (and
      (on c d)
      (on b a)
    )
  )
)
